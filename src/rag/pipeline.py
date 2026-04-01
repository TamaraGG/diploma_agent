# --- Пример использования ---
import asyncio
import os.path

from langchain_community.embeddings import HuggingFaceEmbeddings

from src.rag.chunking.markdown_converter import UniversalConverter
from src.rag.chunking.markdown_splitting import DoclingMarkdownProcessor
from src.rag.ingestion.vector_db.hybrid_vector_store import HybridVectorStore, HybridSearchConfigData

FILES = [r"C:\Users\gonch\PycharmProjects\DiplomaAgent\data\methodolody\Metodol_21.pdf",
         r"C:\Users\gonch\PycharmProjects\DiplomaAgent\data\methodolody\Методологические комментарии к таблицам _ Банк России.html",
         r"C:\Users\gonch\PycharmProjects\DiplomaAgent\data\methodolody\Polozhenie_Banka_Rossii_Ot_24_11_2022_n_809-P_red_Ot_17_06_docx.docx",
         r"C:\Users\gonch\PycharmProjects\DiplomaAgent\data\methodolody\Ukazanie_Banka_Rossii_Ot_10_04_2023_n_6406-U_red_Ot_10_11.docx"]

QUESTIONS = [
    "Учитываются ли нерезиденты в задолженности организаций в региональном разрезе?", # +
    "Существует ли статистика на сайте ЦБ по задолженности организаций малого и среднего предпринимательства?", # +
    "В каких разрезах можно посмотреть задолженность организаций, относящихся к МСП?", # +
    "Как часто и по какому графику обновляется информация о задолженности ЮЛ и ИП на сайте Банка России?", # -
    "Входит ли задолженность ИП, отраженную в статистике  Банка России, задолженность ИП как физического лица?", # -
    "По какому правилу заемщик относится субъекту РФ?", # +
    "Учитываются ли в задолженности ЮЛ начисленные проценты?", # +
    "Какие учреждения учитываются в статистике задолженности госсектора?", # +
    "Как подсчитывается количество заемщиков в статистике ЦБ по кредитам?", # +
    "Учитываются ли в статистике Банка России по задолженности ЮЛ и ИП ликвидированные компании и компании на стадии банкротства?", # -
    "Как отражаются в статистике ЦБ по задолженности компании-редомецилянты?" # +

]

async def main():
    # # Настройка процессора
    # processor = DoclingMarkdownProcessor(
    #     max_tokens=512,
    #     merge_peers=True,
    #     enrich_metadata=True
    # )
    #
    # md_converter = UniversalConverter()
    #
    # print(f"\n\n=== ПЕРЕВОДИМ ФАЙЛЫ В .MD ===\n\n")
    #
    # for file in FILES:
    #     print(f"== начинаем обработку {file} ==")
    #     if not os.path.exists(file+".md"):
    #         print(f"== файла не существует, поэтому конвертируем ==")
    #         md_converter.convert(file, file+".md")
    #     print(f"== закончили обработку {file} ==")
    #
    embeddings = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-small",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    hybrid_store = HybridVectorStore(
        collection_name="documents",
        embeddings=embeddings,  # Передаем явно
        config=HybridSearchConfigData(
            enable_dense=True,
            enable_sparse=True,
            bm25_text_config="russian",
            final_k=10,
        )
    )
    # await hybrid_store.initialize(recreate=True)
    #
    # print(f"\n\n=== СОХРАНЯЕМ ЧАНКИ В БД ===\n\n")
    #
    # for file in FILES:
    #     print(f"== начинаем обработку {file} ==")
    #     try:
    #         docs = processor.process_file(file+".md")
    #         print(f"Создано чанков из {file}.md: {len(docs)}\n")
    #
    #         ids = await hybrid_store.add_documents(docs)
    #         print(f"Добавлено документов для {file}: {len(ids)}")
    #
    #     except Exception as e:
    #         print(f"Ошибка при обработке {file}.md: \n{e}")
    #     print(f"== закончили обработку {file} ==")
    #
    print(f"\n\n=== ЗАПРОС В БД ===\n\n")

    await hybrid_store.initialize(recreate=False)

    for question in QUESTIONS:
        results = await hybrid_store.search(question, k=5)
        print(f"\n\n\n=======================\n"
              f"[question]: {question}"
              f"\n========\n")
        print(f"[texts]: \n\n")
        for doc in results:
            print(f"------\n{doc.page_content}\n")

if __name__ == "__main__":
    asyncio.run(main())