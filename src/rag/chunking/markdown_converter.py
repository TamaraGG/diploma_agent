from pathlib import Path

from src.rag.chunking.file_2_markdown.base_2_markdown_converter import Base2MarkdownConverter
from src.rag.chunking.file_2_markdown.docs_2_markdown_converter import Docx2MarkdownConverter
from src.rag.chunking.file_2_markdown.html_2_markdown_converter import Html2MarkdownConverter
from src.rag.chunking.file_2_markdown.pdf_2_markdown_converter import Pdf2MarkdownConverter


class UniversalConverter:
    def __init__(self):
        self.pdf_converter = Pdf2MarkdownConverter(batch_size=10)
        self.docx_converter = Docx2MarkdownConverter()
        self.html_converter = Html2MarkdownConverter()
        self.default_converter = Base2MarkdownConverter()

        self.extension_map = {
            ".pdf": self.pdf_converter,
            ".docx": self.docx_converter,
            ".html": self.html_converter
        }

    def convert(self, input_file: str, output_file: str) -> None:
        suffix = Path(input_file).suffix.lower()

        converter = self.extension_map.get(suffix)

        if not converter:
            converter = self.default_converter
            print(f"Для файлов '{suffix}' не определено специального конвертера, "
                  f"поэтому к нему будет применен дефолтный.")

        converter.convert(input_file, output_file)