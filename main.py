from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright

from src.web_scrapers.get_web_pages import get_web_pages
from src.web_scrapers.WebFilesLoader import WebFilesLoader
from src.web_scrapers.models import WebPage

CONFIG_PATH = "src/web_scrapers/config.yaml"

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

if __name__ == '__main__':

    pages_list: list[WebPage] = get_web_pages(CONFIG_PATH)

    for web_page in pages_list[1:2]:
        print(f"\n\n=== начинаем обработку страницы {web_page.url}\n\n")
        file_loader = WebFilesLoader(web_page.url)
        try:
            if file_loader._is_url_file(web_page.url):
                print(f"Найдено ссылок: {1}")
                # print(f"Найдена ссылка: {web_page.url}")
            else:
                for path in web_page.paths:
                    print(f"\n\n= начинаем обработку пути {path}\n\n")
                    last_locator = file_loader.follow_path(path)
                    if last_locator:
                        links = file_loader.find_files(last_locator, [".xlsx", ".xls"])
                        print(f"Найдено ссылок: {len(links)}")
                        # for l in links:
                        #     print(f"Найдена ссылка: {l}")
                        # print("-----------------")
                    else:
                        print(f"Не удалось проследовать по пути.")
        finally:
            file_loader.close()
