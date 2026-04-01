import json
from pathlib import Path
from typing import Iterable
from langchain_core.documents import Document

def save_documents_to_jsonl(documents: Iterable[Document], output_file: str):

    output_path: Path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(output_path, 'w', encoding='utf-8') as f:
        for doc in documents:
            entry = {
                "page_content": doc.page_content,
                "metadata": doc.metadata
            }
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            count += 1
    print(f"Успешно сохранено {count} чанков: {output_path}")