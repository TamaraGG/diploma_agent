from src.file_loading.loader.web_file_loader import WebFileLoader
from src.file_loading.models.models import WebPage, Document
from src.file_loading.functions.get_web_pages import get_web_pages
from src.file_loading.scraper.sbr_scraper.sbr_scraper import SbrScraper

CONFIG_PATH = "src/file_loading/config.yaml"

if __name__ == '__main__':

    pages_list: list[WebPage] = get_web_pages(CONFIG_PATH)
    files_links: list[Document] = []

    # GET ALL LINKS
    for web_page in pages_list:
        print(f"\n\n=== начинаем обработку страницы {web_page.url}\n\n")
        with SbrScraper(web_page.url) as file_loader:
            links = []
            try:
                if file_loader.is_url_file(web_page.url):
                    links = [Document(load_date=None,
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
            except Exception as e:
                raise Exception(f"ошибка во время обработки {web_page.name}: \nошибка: {e}")
            files_links += links

    # MANAGE VERSIONS


    # LOAD FILES BY LINKS
    for link in files_links:
        WebFileLoader.load_file(link.url, f"downloads")

