from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, Page, Locator, BrowserContext, Browser, Playwright

class WebFilesLoader:
    def __init__(self, url: str):
        self.url = url
        self.playwright: Playwright = sync_playwright().start()

        self.browser: Browser = self.playwright.chromium.launch(headless=False, slow_mo=300)
        self.context: BrowserContext = self.browser.new_context()
        self.page: Page = self.context.new_page()

        if not self._is_url_file(self.url):
            self.page.goto(self.url)

    def follow_path(self, path_list: list[str]) -> Locator | None:
        """
        Прокликивает все элементы пути, ища каждый следующий внутри предыдущего.
        Возвращает последний локатор.
        """
        result: Locator | None = None
        try:
            current_locator = self.page.locator("body")

            for path in path_list:
                current_locator = current_locator.locator("*").filter(has_text=path)

                step_element = current_locator.last
                step_element.wait_for(state="visible")

                if not self._is_locator_file(step_element):
                    print(f"Кликнули по: {path}.")
                    step_element.click()
                else:
                    print(f"{path} - ссылка на скачивание файла. Не кликаем на нее.")

            result = current_locator.last

        except Exception as e:
            print(f"Не удалось пройти по пути.\nerror: {e}")

        self.page.reload()
        return result

    def find_files(self, where: str, file_types: list[str]) -> list[str]:
        """Возвращает ссылки на все ближайшие к тексту where файлы"""
        if self._is_url_file(self.url):
            return [self.url]
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

        href = locator.get_attribute("href") or None
        if href and self._is_url_file(urljoin(self.url, href)):
            return [urljoin(self.url, href)]

        all_links = locator.locator("a").all()
        valid_files = []

        if not file_types:
            file_types = []

        for link in all_links:
            href = link.get_attribute("href")
            if not href:
                continue

            full_url = urljoin(self.url, href)
            is_file = self._is_url_file(full_url, file_types)




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


    def _is_url_file(self, url: str, file_types: list[str] | None = None) -> bool:
        if not url:
            return False
        if not file_types:
            file_types = ['.xlsx', '.xls', '.csv', '.zip', '.pdf', '.doc', '.docx']

        clean_url = url.split('?')[0].lower()
        if any(clean_url.endswith(ext) for ext in file_types):
            return True

        try:
            response = self.page.request.head(url, timeout=5000)
            # content_type = response.headers.get('content-type', '').lower()
            content_disp = response.headers.get('content-disposition', '').lower()

            if "attachment" in content_disp:
                return True

        except Exception as e:
            print(f"Не удалось проверить URL {url}: {e}")

        return False

    def close(self):
        self.browser.close()
        self.playwright.stop()

