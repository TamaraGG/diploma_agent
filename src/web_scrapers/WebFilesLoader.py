import os
from urllib.parse import urljoin

import requests
from playwright.sync_api import sync_playwright, Page, Locator, BrowserContext, Browser, Playwright

class WebFilesLoader:
    def __init__(self, url: str):
        self.url = url
        self.playwright: Playwright = sync_playwright().start()

        self.browser: Browser = self.playwright.chromium.launch(headless=False, slow_mo=300)
        self.context: BrowserContext = self.browser.new_context()
        self.page: Page = self.context.new_page()


    def change_url(self, url: str):
        self.url = url
        self.page.goto(self.url)
        if not self._is_url_file(self.url):
            self.page.goto(self.url)

    def follow_path(self, path_list: list[str]) -> bool:
        """Прокликивает все элемены пути"""
        try:
            for path in path_list:
                element = self.page.get_by_text(path, exact=True).first

                element.wait_for(state="visible", timeout=5000)
                if not self._is_locator_file(element):
                    element.click()
                    print(f"Кликнули по: {path}.")
                else:
                    print(f"{path} - ссылка на скачивание файла. Не кликаем на нее.")
                    return False
        except Exception as e:
            print(f"Не удалось кликнуть по заголовку.\nerror: {e}")
            return False
        return True


    def find_files(self, where: str, file_types: list[str]) -> list[str]:
        """Возвращает ссылки на все ближайшие к тексту where файлы"""
        try:
            locator = self.page.get_by_text(where)
            while 1:
                links = self._get_locator_files(locator)
                if links:
                    return links
                locator = locator.locator("..")
                print(f"Не нашли файлы в текущем элементе, поднимаемся на уровень выше.")

        except Exception as e:
            print(f"Не удалось найти файлы типа {file_types} в секции {where} (из-за ошибки \n{e} )")
        return []

    def _get_locator_files(self, locator: Locator, file_types: list[str] | None = None) -> list[str]:
        """Возвращает все файлы в локаторе."""
        all_links = locator.locator("a").all()
        valid_files = []

        if not file_types:
            file_types = []

        for link in all_links:
            href = link.get_attribute("href")
            if not href:
                continue

            full_url = urljoin(self.url, href)
            link_text = link.inner_text().lower()
            link_class = link.get_attribute("class") or ""
            is_file = False

            if any(ext in href.lower() for ext in file_types):
                is_file = True
            elif any(keyword in link_text for keyword in ['скачать', ' мб', ' кб'] + file_types):
                is_file = True
            elif "file" in link_class.lower():
                is_file = True
            else:
                try:
                    response = self.page.request.head(full_url, timeout=10000)
                    content_type = response.headers.get('content-type', '').lower()
                    content_disp = response.headers.get('content-disposition', '').lower()
                    if "attachment" in content_disp or "spreadsheet" in content_type or "excel" in content_type:
                        is_file = True
                except Exception as e:
                    print(f"Тайм-аут или ошибка при проверке ссылки {full_url}: {e}")

            if is_file:
                if full_url not in valid_files:
                    valid_files.append(full_url)

        return valid_files

    def _is_locator_file(self, locator : Locator) -> bool:
        try:
            with self.page.expect_download(timeout=3000) as download_info:
                locator.click(modifiers=["Control"])
            download = download_info.value
            download.cancel()
            return True
        except:
            locator.click()
            return False

    def _is_url_file(self, url: str) -> bool:
        if not url:
            return False

        full_url = urljoin(self.page.url, url)

        clean_url = full_url.split('?')[0].lower()
        file_extensions = ['.xlsx', '.xls', '.csv', '.zip', '.pdf', '.doc', '.docx']

        if any(clean_url.endswith(ext) for ext in file_extensions):
            return True

        try:
            response = self.page.request.head(full_url, timeout=5000)

            # content_type = response.headers.get('content-type', '').lower()
            content_disp = response.headers.get('content-disposition', '').lower()

            if "attachment" in content_disp:
                return True

        except Exception as e:
            print(f"Не удалось проверить URL {full_url}: {e}")

        return False

    def close(self):
        self.browser.close()
        self.playwright.stop()

