import os
from typing import List, Optional
from pathlib import Path

from docling.document_converter import DocumentConverter
from docling.chunking import HierarchicalChunker
from langchain_core.documents import Document
from markdownify import MarkdownConverter

from src.rag.chunking.markdown_converter import UniversalConverter


class DoclingMarkdownProcessor:
    def __init__(
            self,
            max_tokens: int = 2000,
            min_tokens: int = 400,
            merge_peers: bool = True,
            merge_list_items: bool = True,
            enrich_metadata: bool = True
    ):
        self.converter = DocumentConverter()
        self.chunker = HierarchicalChunker(
            max_tokens=max_tokens,
            merge_peers=merge_peers,
        )
        self.enrich_metadata = enrich_metadata
        self.max_tokens = max_tokens
        self.min_tokens = min_tokens

    def process_file(self, file_path: str) -> List[Document]:

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        result = self.converter.convert(file_path)
        dl_doc = result.document

        raw_chunks = list(self.chunker.chunk(dl_doc))

        merged_chunks = self._merge_small_chunks(raw_chunks)

        return self._create_langchain_documents(merged_chunks, Path(file_path).name)

    def _merge_small_chunks(self, chunks):

        if not chunks:
            return []

        refined = []
        current_chunk = None

        for chunk in chunks:
            if current_chunk is None:
                current_chunk = chunk
                continue

            same_hierarchy = getattr(current_chunk.meta, "headings", []) == getattr(chunk.meta, "headings", [])
            under_limit = (len(current_chunk.text.split()) + len(chunk.text.split())) < self.max_tokens

            if same_hierarchy and under_limit:
                # Склеиваем текст (добавляем разделитель)
                current_chunk.text += "\n\n" + chunk.text
            else:
                refined.append(current_chunk)
                current_chunk = chunk

        if current_chunk:
            refined.append(current_chunk)

        return refined

    def _create_langchain_documents(self, chunks, file_name: str) -> List[Document]:
        lc_documents = []

        for chunk in chunks:
            headings = getattr(chunk.meta, "headings", [])
            hierarchy_path = " > ".join(headings) if headings else "General"

            # Текст чанка
            content = chunk.text

            # Chunk Enrichment
            if self.enrich_metadata:
                header_info = f"SOURCE: {file_name}\nSECTION: {hierarchy_path}"
                content = f"{header_info}\n\n{content}"

            metadata = {
                "source": file_name,
                "hierarchy": hierarchy_path,
                "headings": headings,
            }

            lc_documents.append(Document(page_content=content, metadata=metadata))

        return lc_documents


