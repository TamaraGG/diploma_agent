import os
from dataclasses import dataclass
from typing import Any

from langchain_community.embeddings import GigaChatEmbeddings
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pgvec_textsearch import (HybridSearchConfig,
                                        DistanceStrategy,
                                        PGVecTextSearchEngine,
                                        PGVecTextSearchStore,
                                        HNSWIndex, BM25Index, reciprocal_rank_fusion)


@dataclass
class HybridSearchConfigData:
    enable_dense: bool = True
    enable_sparse: bool = True
    dense_top_k: int = 20
    sparse_top_k: int = 20
    rrf_k: int = 60
    final_k: int = 10

    bm25_text_config: str = "russian"
    bm25_k1: float = 1.2
    bm25_b: float = 0.75

    hnsw_m: int = 16
    hnsw_ef_construction: int = 64
    distance_strategy: DistanceStrategy = DistanceStrategy.COSINE_DISTANCE


class HybridVectorStore:
    def __init__(self,
                 connection_string: str | None = None,
                 collection_name: str = "documents",
                 embeddings: Embeddings | None = None,
                 config: HybridSearchConfigData | None = None):

        self.collection_name = collection_name
        self.config = config or HybridSearchConfigData()

        if connection_string is None:
            connection_string = self._build_connection_string()
        self.connection_string = connection_string

        self.embeddings = embeddings or self._default_embeddings()
        self.embedding_dim = self._get_embedding_dimension()

        self._engine: PGVecTextSearchEngine | None = None
        self._store: PGVecTextSearchStore | None = None

    def _build_connection_string(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{os.getenv('POSTGRES_USER', 'postgres')}:"
            f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
            f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
            f"{os.getenv('POSTGRES_PORT', '5432')}/"
            f"{os.getenv('POSTGRES_DB', 'timescaledb')}"
        )

    def _default_embeddings(self) -> Embeddings:
        return HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-small",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

    def _get_embedding_dimension(self) -> int:
        if isinstance(self.embeddings, GigaChatEmbeddings):
            return 384
        return 512

    async def initialize(self, recreate: bool = False) -> "HybridVectorStore":

        # Создаем движок
        self._engine = PGVecTextSearchEngine.from_connection_string_async(
            self.connection_string
        )

        if recreate:
            await self._engine.adrop_table(self.collection_name)

        await self._engine.ainit_hybrid_vectorstore_table(
            table_name=self.collection_name,
            vector_size=self.embedding_dim,
            hnsw_index=HNSWIndex(
                m=self.config.hnsw_m,
                ef_construction=self.config.hnsw_ef_construction,
                distance_strategy=self.config.distance_strategy,
            ),
            bm25_index=BM25Index(
                text_config=self.config.bm25_text_config,
                k1=self.config.bm25_k1,
                b=self.config.bm25_b,
            ),
        )

        self._vectorstore = await PGVecTextSearchStore.create(
            engine=self._engine,
            embedding_service=self.embeddings,
            table_name=self.collection_name,
        )

        hybrid_config = HybridSearchConfig(
            enable_dense=self.config.enable_dense,
            enable_sparse=self.config.enable_sparse,
            dense_top_k=self.config.dense_top_k,
            sparse_top_k=self.config.sparse_top_k,
            fusion_function=reciprocal_rank_fusion,
            fusion_function_parameters={"rrf_k": self.config.rrf_k},
        )

        self._store = await PGVecTextSearchStore.create(
            engine=self._engine,
            embedding_service=self.embeddings,
            table_name=self.collection_name,
            hybrid_search_config=hybrid_config,
        )

        return self

    async def add_documents(
            self,
            documents: list[Document],
            batch_size: int = 100) -> list[str]:

        if not self._store:
            raise RuntimeError("Хранилище не инициализировано. Вызовите initialize()")

        all_ids = []
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            ids = await self._store.aadd_documents(batch)
            all_ids.extend(ids)

        return all_ids

    async def add_texts(
            self,
            texts: list[str],
            metadatas: list[dict[str, Any]] | None = None) -> list[str]:

        documents = []
        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas else {}
            documents.append(Document(page_content=text, metadata=metadata))

        return await self.add_documents(documents)

    async def search(
            self,
            query: str,
            k: int | None = None,
            **kwargs) -> list[Document]:

        if not self._store:
            raise RuntimeError("Хранилище не инициализировано. Вызовите initialize()")

        final_k = k or self.config.final_k

        results = await self._store.asimilarity_search(query, k=final_k, **kwargs)
        return results

    async def search_with_scores(
            self,
            query: str,
            k: int | None = None,
            **kwargs) -> list[tuple[Document, float]]:

        if not self._store:
            raise RuntimeError("Хранилище не инициализировано. Вызовите initialize()")

        final_k = k or self.config.final_k

        results = await self._store.asimilarity_search_with_score(
            query, k=final_k, **kwargs
        )
        return results

    def as_retriever(self, **kwargs) -> BaseRetriever:

        if not self._store:
            raise RuntimeError("Хранилище не инициализировано. Вызовите initialize()")

        return self._store.as_retriever(**kwargs)

    async def delete_collection(self) -> None:
        if self._engine:
            await self._engine.adrop_table(self.collection_name)

    async def get_document_count(self) -> int:
        if not self._store:
            return 0

        async with self._engine._async_engine.connect() as conn:
            result = await conn.execute(
                f"SELECT COUNT(*) FROM {self.collection_name}"
            )
            return result.scalar()

    def __repr__(self) -> str:
        return f"HybridVectorStore(collection={self.collection_name})"

