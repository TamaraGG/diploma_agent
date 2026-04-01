from src.data_files_loading.functions.save_time import save_time
from src.data_files_loading.loader.web_file_loader import WebFileLoader
from src.data_files_loading.models.models import WebPage, DocumentVersion, Document
from src.data_files_loading.functions.get_web_pages import get_web_pages
from src.data_files_loading.scraper.sbr_scraper.sbr_scraper import SbrScraper
from src.data_files_loading.version_manager.version_manager import VersionManager

CONFIG_PATH = "src/data_files_loading/config.yaml"

if __name__ == '__main__':

    pages_list: list[WebPage] = get_web_pages(CONFIG_PATH)
    files_links: list[DocumentVersion] = []
    documents: list[Document] = []
    # GET ALL LINKS
    for web_page in pages_list:
        print(f"\n\n=== начинаем обработку страницы {web_page.url}\n\n")
        with SbrScraper(web_page.url) as file_loader:
            links = []
            try:
                if file_loader.is_url_file(web_page.url):
                    links = [DocumentVersion(load_date=None,
                                             url=web_page.url,
                                             name="")]
                else:
                    for path in web_page.paths:
                        print(f"\n\n= начинаем обработку пути {path}\n\n")
                        if file_loader.follow_path(path):
                            links = file_loader.get_all_documents()
                        else:
                            print(f"Не удалось проследовать по пути.")
                        file_loader.reset()
                        print(f"Найдено файлов: {len(links)}")
                        documents.append(Document(name=path[-1] if path else "",
                                                  versions=links))
            except Exception as e:
                raise Exception(f"ошибка во время обработки {web_page.name}: \nошибка: {e}")
        files_links += links

    # MANAGE VERSIONS
    print(f"num of docs: {len(documents)}")
    versions = VersionManager.get_last_common_month(documents)

    # LOAD FILES BY LINKS
    for version in versions:
        WebFileLoader.load_file(version.url, f"downloads")

    save_time()