from datetime import datetime

from src.file_loading.models.models import DocumentVersions
from src.file_loading.version_manager.base_version_manager import BaseVersionManager


class VersionManager(BaseVersionManager):
    @staticmethod
    def get_latest_version(documents: list[DocumentVersions]) -> datetime | None:
        if not documents:
            return None

        same_versions: set[datetime] = set(documents.pop().versions.items())
        for document in documents:
            same_versions.intersection(document.versions.items())
        sorted(same_versions, reverse=True)
        return same_versions.pop() if same_versions else None