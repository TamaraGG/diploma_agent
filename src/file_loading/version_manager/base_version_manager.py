from abc import ABC, abstractmethod

from src.file_loading.models.models import DocumentVersions, Document


class BaseVersionManager(ABC):
    @staticmethod
    @abstractmethod
    def get_latest_version(documents: list[DocumentVersions]) -> list[Document]:
        pass