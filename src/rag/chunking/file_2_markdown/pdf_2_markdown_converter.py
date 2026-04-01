import re
import gc
import shutil
from pathlib import Path

from docling_core.types.doc import DocItemLabel
from pypdf import PdfReader, PdfWriter
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from typing_extensions import LiteralString

from src.rag.chunking.file_2_markdown.base_2_markdown_converter import Base2MarkdownConverter

try:
    from hierarchical.postprocessor import ResultPostprocessor
except ImportError:
    ResultPostprocessor = None
    print("Внимание: ResultPostprocessor не найден. Иерархия будет стандартной.")


class Pdf2MarkdownConverter(Base2MarkdownConverter):
    def __init__(self, batch_size=10):
        super().__init__()
        self.batch_size = batch_size
        options = PdfPipelineOptions()
        options.do_ocr = False
        options.generate_page_images = False

        self.converter = DocumentConverter(
            format_options={"pdf": PdfFormatOption(pipeline_options=options)}
        )

        self.header_stack: dict[int, str | None] = {i: None for i in range(1, 7)}
        self.is_first_batch = True

    def _manual_md_render(self, doc):
        md_lines = []
        pending_header_level = None
        pending_header_text = []

        def flush_header():
            nonlocal pending_header_level, pending_header_text
            if pending_header_level:
                full_text = " > ".join(pending_header_text).strip()

                md_lines.append(f"{'#' * pending_header_level} {full_text}")

                self.header_stack[pending_header_level] = full_text
                for i in range(pending_header_level + 1, 7):
                    self.header_stack[i] = None

                pending_header_level = None
                pending_header_text = []

        for item, _ in doc.iterate_items():
            if item.label == DocItemLabel.SECTION_HEADER:
                current_level = getattr(item, 'level', 1)
                if current_level < 1: current_level = 1

                if pending_header_level == current_level:
                    pending_header_text.append(item.text.strip())
                else:
                    flush_header()
                    pending_header_level = current_level
                    pending_header_text = [item.text.strip()]

            else:
                flush_header()

                if item.label == DocItemLabel.TEXT:
                    md_lines.append(item.text)
                elif item.label == DocItemLabel.LIST_ITEM:
                    md_lines.append(f"- {item.text}")
                elif item.label == DocItemLabel.TABLE:
                    try:
                        md_lines.append(item.export_to_markdown())
                    except:
                        md_lines.append("\n[Таблица]\n")

        flush_header()
        return "\n\n".join(md_lines)

    def _get_breadcrumb_prefix(self, current_md) -> LiteralString:
        if re.match(r'^#{1,2,3}\s', current_md.lstrip()):
             return ""

        prefix = []
        for l in range(1, 7):
            if self.header_stack[l]:
                prefix.append(f"{'#' * l} {self.header_stack[l]} (продолжение)")
        return "\n\n".join(prefix) + "\n\n" if prefix else ""

    def convert(self, input_file: str, output_file: str) -> None:
        input_pdf = Path(input_file).absolute()
        parts_dir = Path("./pdf_parts")
        if parts_dir.exists(): shutil.rmtree(parts_dir)
        parts_dir.mkdir(exist_ok=True)

        reader = PdfReader(str(input_pdf))
        total_pages = len(reader.pages)
        output_blocks = []

        for start in range(0, total_pages, self.batch_size):
            end = min(start + self.batch_size, total_pages)
            part_file = parts_dir / f"p_{start + 1}.pdf"

            writer = PdfWriter()
            for i in range(start, end):
                writer.add_page(reader.pages[i])
            with open(part_file, "wb") as f:
                writer.write(f)

            result = self.converter.convert(str(part_file))
            if ResultPostprocessor:
                try:
                    ResultPostprocessor(result).process()
                except:
                    pass

            batch_md = self._manual_md_render(result.document)

            if not self.is_first_batch:
                prefix = self._get_breadcrumb_prefix(batch_md)
                output_blocks.append(prefix + batch_md)
            else:
                output_blocks.append(batch_md)
                self.is_first_batch = False

            del result
            gc.collect()

        if parts_dir.exists(): shutil.rmtree(parts_dir)

        full_md = "\n\n---\n\n".join(output_blocks)
        self._save_md(full_md, output_file)

