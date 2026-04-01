from langchain_core.documents import Document

from src.rag.chunking.chunk_data import chunk_data


async def build_knowledge_graph(
        docs: list[Document]
):

    graphiti = Graphiti(
        conn_config=()
    )

    for i, doc in enumerate(docs):

