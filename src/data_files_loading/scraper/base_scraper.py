from abc import ABC, abstractmethod

from playwright.sync_api import Locator

from src.data_files_loading.models.models import DocumentVersion


class BaseScraper(ABC):
    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def follow_path(self, path_list: list[str]) -> Locator | None:
        """
        Прокликивает все элементы пути, ища каждый следующий внутри предыдущего.
        Возвращает последний локатор.
        """
        pass

    @abstractmethod
    def get_all_documents(self, file_types: list[str]) -> list[DocumentVersion]:
        """Возвращает ссылки на все ближайшие к текущему локатору файлы."""
        pass

    @abstractmethod
    def reset(self) -> None:
        pass