
from typing import Literal
from urllib.parse import urljoin

from playwright.sync_api import Playwright, Browser, Page, Locator

from src.file_loading.models.models import DocumentVersion
from src.file_loading.scraper.sbr_scraper.strategies import get_date_from_referenceable, \
    get_date_from_versions_item
from src.file_loading.scraper.universal_scraper.universal_scraper import UniversalScraper

LOCATOR_TYPES = Literal["referenceable", "versions_item", "plain"]

class SbrScraper(UniversalScraper):
    def __init__(self, url: str):
        super().__init__(url)

        self.url: str = url

        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None

        self.current_locator: Locator | None = None

        self.date_getters = {
            "referenceable": get_date_from_referenceable,
            "versions_item": get_date_from_versions_item
        }

    def get_all_documents(self, file_types: list[str] | None = None) -> list[DocumentVersion]:
        """Возвращает ссылки на все ближайшие к текущему локатору файлы."""
        if self.is_url_file(self.url):
            return [DocumentVersion(url=urljoin(self.url, self.url),
                                    name=self.url.split("/")[-1],
                                    load_date=None)]
        try:
            while self.current_locator is not self.page.locator("body"):
                links = self._get_document_locators(self.current_locator)
                documents = [self.get_document_from_locator(link) for link in links]
                if documents:
                    return documents

                self.current_locator = self.current_locator.locator("..")
                print(f"Не нашли файлы в текущем элементе, поднимаемся на уровень выше.")

        except Exception as e:
            print(
                f"Не удалось найти файлы типа {file_types} в секции {self.current_locator.inner_text()} (из-за ошибки \n{e} )")
        return []

    @staticmethod
    def type_locator(locator: Locator) -> LOCATOR_TYPES:
        if "referenceable" in locator.get_attribute("class"):
            return "referenceable"
        elif "versions_item" in locator.get_attribute("class"):
            return "versions_item"
        return "plain"


    def get_document_from_locator(self, locator: Locator) -> DocumentVersion | None:
        href = locator.get_attribute("href")
        if not href:
            return None

        loc_type = self.type_locator(locator)
        if loc_type in self.date_getters.keys():
            date = self.date_getters[loc_type](locator)
        else:
            date = None

        full_url = urljoin(self.url, href)
        document = DocumentVersion(url=full_url,
                                   name=href.split('/')[-1],
                                   load_date=date)
        return document
