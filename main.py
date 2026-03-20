from playwright.sync_api import sync_playwright

from src.web_scrapers.FilesLoader import FilesLoader
from src.web_scrapers.get_xlsx import get_links

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
    # with sync_playwright() as p:
    #     browser = p.chromium.launch(headless=False)
    #     page = browser.new_page()
    #     page.goto(URL)
    #     file_loader = FilesLoader(page)
    #     file_loader.navigate_path(PATHS[1])
    #     links = file_loader.get_excel_files()
    #     print(links)
    #     browser.close()
    get_links(URL, PATHS[0])
