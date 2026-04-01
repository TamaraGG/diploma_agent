from abc import ABC, abstractmethod

from src.data_files_loading.models.models import Document, DocumentVersion


class BaseVersionManager(ABC):
    @staticmethod
    @abstractmethod
    def get_latest_version(documents: list[Document]) -> list[DocumentVersion]:
        pass