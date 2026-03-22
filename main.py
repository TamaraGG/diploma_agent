from src.web_scrapers.core.models import WebPage
from src.web_scrapers.get_web_pages import get_web_pages
from src.web_scrapers.scrapers.WebFilesFinder import WebFilesFinder

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

    for web_page in pages_list:
        print(f"\n\n=== начинаем обработку страницы {web_page.url}\n\n")
        file_loader = WebFilesFinder(web_page.url)
        links = []
        try:
            if file_loader._is_url_file(web_page.url):
                links = [web_page.url]
            else:
                for path in web_page.paths:
                    print(f"\n\n= начинаем обработку пути {path}\n\n")
                    if file_loader.follow_path(path):
                        links = file_loader.find_files_links([".xlsx", ".xls"])
                    else:
                        print(f"Не удалось проследовать по пути.")
                    file_loader.reset()
                    print(f"Найдено файлов: {len(links)}")
                    print(links)
        finally:
            file_loader.close()
