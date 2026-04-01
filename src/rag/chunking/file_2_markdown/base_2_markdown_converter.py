from docling.document_converter import DocumentConverter
from hierarchical.postprocessor import ResultPostprocessor


class Base2MarkdownConverter:
    def __init__(self):
        pass

    def convert(self, input_file: str, output_file: str) -> None:
        converter = DocumentConverter()

        result = converter.convert(input_file)

        # if ResultPostprocessor:
        #     ResultPostprocessor(result).process()

        full_markdown = result.document.export_to_markdown()

        self._save_md(full_markdown, output_file)


    def _save_md(self, md_text: str, output_file: str) -> bool:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(md_text)
                return True
        except Exception as e:
            print(f"Не удалось сохранить markdown в файл {output_file}. \n"
                  f"Ошибка: \n{e}")
            return False