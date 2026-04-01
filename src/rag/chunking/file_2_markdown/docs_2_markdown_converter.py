from docling.datamodel.base_models import InputFormat
from docling.document_converter import WordFormatOption, DocumentConverter

from src.rag.chunking.file_2_markdown.base_2_markdown_converter import Base2MarkdownConverter


class Docx2MarkdownConverter(Base2MarkdownConverter):
    def convert(self, input_file: str, output_file: str) -> None:
        word_options = WordFormatOption(
            extract_header_footer=False,
        )
        converter = DocumentConverter(
            allowed_formats=[InputFormat.DOCX],
            format_options={InputFormat.DOCX: word_options}
        )

        result = converter.convert(input_file)
        full_markdown = result.document.export_to_markdown()
        self._save_md(full_markdown, output_file)

