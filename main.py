from src.file_loading.loader.web_file_loader import WebFileLoader
from src.file_loading.models.models import WebPage, Document
from src.file_loading.functions.get_web_pages import get_web_pages
from src.file_loading.scraper.sbr_scraper.sbr_scraper import SbrScraper


URL = "https://www.cbr.ru/statistics/bank_sector/sors/"
PATHS = [
    [
        "Кредиты, предоставленные юридическим лицам - резидентам и индивидуальным предпринимателям (в целом по Российской Федерации) ",
        "Информация о количестве заемщиков и предоставленных кредитов"
    ],
    [
        "Кредиты, предоставленные юридическим лицам - резидентам и индивидуальным предпринимателям (региональный разрез)",
        "Задолженность, в том числе просроченная, по кредитам, предоставленным юридическим лицам — резидентам и индивидуальным предпринимателям, по видам экономической деятельности и отдельным направлениям использования средств (на дату)"
    ]
]
CONFIG_PATH = "src/file_loading/config.yaml"

if __name__ == '__main__':

    pages_list: list[WebPage] = get_web_pages(CONFIG_PATH)

    for web_page in pages_list:
        print(f"\n\n=== начинаем обработку страницы {web_page.url}\n\n")
        with WebFilesFinder(web_page.url) as file_loader:
            links = []
            try:
                if file_loader.is_url_file(web_page.url):
                    links = [web_page.url]
                else:
                    for path in web_page.paths:
                        print(f"\n\n= начинаем обработку пути {path}\n\n")
                        if file_loader.follow_path(path):
                            links = file_loader.get_all_documents([".xlsx", ".xls"])
                        else:
                            print(f"Не удалось проследовать по пути.")
                        file_loader.reset()
                        print(f"Найдено файлов: {len(links)}")
                        print(links)
            finally:
                file_loader.close()
