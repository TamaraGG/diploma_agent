from abc import ABC, abstractmethod

from playwright.sync_api import Locator

from src.web_scrapers.core.models import Document


class BaseScraper(ABC):
    @abstractmethod
    def follow_path(self, path_list: list[str]) -> Locator | None:
        """
        Прокликивает все элементы пути, ища каждый следующий внутри предыдущего.
        Возвращает последний локатор.
        """
        pass

    @abstractmethod
    def find_files_links(self, file_types: list[str]) -> list[Document]:
        """Возвращает ссылки на все ближайшие к текущему локатору файлы."""
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass