from langchain_core.documents import Document

from src.rag.chunking.old.split_data_to_chunks import split_data_to_chunks


async def build_knowledge_graph(
        docs: list[Document]
):

    graphiti = Graphiti(
        conn_config=()
    )

    for i, doc in enumerate(docs):
        pass

