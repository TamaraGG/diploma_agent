import os
from dataclasses import dataclass
from typing import Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_pgvec_textsearch import PGVecTextSearchStore, DistanceStrategy, PGVecTextSearchEngine, HNSWIndex, \
    BM25Index, HybridSearchConfig, reciprocal_rank_fusion


@dataclass
class HybridSearchConfigData:
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


class HybridPGVectorStore(PGVecTextSearchStore):

    _dense_store: PGVecTextSearchStore
    _sparse_store: PGVecTextSearchStore

    @classmethod
    async def ainitialize(
            cls,
            embeddings: Embeddings,
            connection_string: str | None = None,
            collection_name: str = "documents",
            config: HybridSearchConfigData | None = None,
            recreate: bool = False,
    ) -> "HybridPGVectorStore":
        config = config or HybridSearchConfigData()

        if connection_string is None:
            connection_string = (
                f"postgresql+asyncpg://"
                f"{os.getenv('POSTGRES_USER', 'postgres')}:"
                f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
                f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
                f"{os.getenv('POSTGRES_PORT', '5432')}/"
                f"{os.getenv('POSTGRES_DB', 'timescaledb')}"
            )

        # Стандартный LangChain-подход: динамическое определение размерности 
        # (чтобы избежать хардкода под конкретные модели)
        embedding_dim = len(embeddings.embed_query("test"))

        engine = PGVecTextSearchEngine.from_connection_string_async(connection_string)

        if recreate:
            await engine.adrop_table(collection_name)

        await engine.ainit_hybrid_vectorstore_table(
            table_name=collection_name,
            vector_size=embedding_dim,
            hnsw_index=HNSWIndex(
                m=config.hnsw_m,
                ef_construction=config.hnsw_ef_construction,
                distance_strategy=config.distance_strategy,
            ),
            bm25_index=BM25Index(
                text_config=config.bm25_text_config,
                k1=config.bm25_k1,
                b=config.bm25_b,
            ),
        )

        hybrid_config = HybridSearchConfig(
            enable_dense=True, enable_sparse=True,
            dense_top_k=config.dense_top_k, sparse_top_k=config.sparse_top_k,
            fusion_function=reciprocal_rank_fusion,
            fusion_function_parameters={"rrf_k": config.rrf_k},
        )
        dense_config = HybridSearchConfig(
            enable_dense=True, enable_sparse=False, dense_top_k=config.dense_top_k
        )
        sparse_config = HybridSearchConfig(
            enable_dense=False, enable_sparse=True, sparse_top_k=config.sparse_top_k
        )

        # 1. Инициализируем ОСНОВНОЙ инстанс как гибридный.
        # Метод cls.create вызывает фабрику базового класса PGVecTextSearchStore,
        # возвращая объект нашего дочернего класса UnifiedPGVectorStore.
        main_store = await cls.create(
            engine=engine,
            embedding_service=embeddings,
            table_name=collection_name,
            hybrid_search_config=hybrid_config
        )

        # 2. Создаем легковесные инстансы для чистых режимов. 
        # Они используют ТОТ ЖЕ engine (один пул подключений к БД), поэтому
        # не потребляют дополнительных ресурсов, но решают проблему потокобезопасности.
        main_store._dense_store = await PGVecTextSearchStore.create(
            engine=engine, embedding_service=embeddings, table_name=collection_name, hybrid_search_config=dense_config
        )
        main_store._sparse_store = await PGVecTextSearchStore.create(
            engine=engine, embedding_service=embeddings, table_name=collection_name, hybrid_search_config=sparse_config
        )

        return main_store

    # =========================================================================
    # МАРШРУТИЗАЦИЯ ПОИСКА
    # Всё остальное (add_texts, add_documents, удаление и т.д.) мы НЕ переопределяем. 
    # Они идеально работают напрямую из базового PGVecTextSearchStore!
    # =========================================================================

    def _get_target_store(self, kwargs: dict) -> PGVecTextSearchStore:
        """
        Перехватывает кастомный аргумент search_mode и извлекает его из kwargs.
        Возвращает нужный инстанс хранилища.
        """
        search_mode = kwargs.pop("search_mode", "hybrid")
        if search_mode == "dense":
            return self._dense_store
        elif search_mode == "sparse":
            return self._sparse_store
        return self  # Возвращаем себя (гибрид по умолчанию)

    def similarity_search(self, query: str, k: int = 4, **kwargs: Any) -> list[Document]:
        target = self._get_target_store(kwargs)
        if target is self:
            return super().similarity_search(query, k=k, **kwargs)
        return target.similarity_search(query, k=k, **kwargs)

    async def asimilarity_search(self, query: str, k: int = 4, **kwargs: Any) -> list[Document]:
        target = self._get_target_store(kwargs)
        if target is self:
            return await super().asimilarity_search(query, k=k, **kwargs)
        return await target.asimilarity_search(query, k=k, **kwargs)

    def similarity_search_with_score(self, query: str, k: int = 4, **kwargs: Any) -> list[tuple[Document, float]]:
        target = self._get_target_store(kwargs)
        if target is self:
            return super().similarity_search_with_score(query, k=k, **kwargs)
        return target.similarity_search_with_score(query, k=k, **kwargs)

    async def asimilarity_search_with_score(self, query: str, k: int = 4, **kwargs: Any) -> list[
        tuple[Document, float]]:
        target = self._get_target_store(kwargs)
        if target is self:
            return await super().asimilarity_search_with_score(query, k=k, **kwargs)
        return await target.asimilarity_search_with_score(query, k=k, **kwargs)