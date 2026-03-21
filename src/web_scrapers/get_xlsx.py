import os

from playwright.sync_api import sync_playwright, Page, Locator

PATHS = {
    "https://www.cbr.ru/statistics/bank_sector/sors/": "",
    "https://www.cbr.ru/statistics/bank_sector/review/": "",
}



def follow_path(page: Page, path_list: list[str]) -> Locator:
    """Прокликивает все элемены пути"""
    try:
        for path in path_list:
            page.get_by_text(path).click()
    except Exception as e:
        print(f"Не удалось кликнуть по заголовку.\nerror: {e}")

def find_files(where: str, file_type: list[str]) -> list[str]:
