from abc import ABC, abstractmethod

from src.file_loading.models.models import DocumentVersion, Document


class BaseVersionManager(ABC):
    @staticmethod
    @abstractmethod
    def get_latest_version(documents: list[DocumentVersion]) -> list[Document]:
        pass