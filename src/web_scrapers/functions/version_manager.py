from datetime import date

from src.web_scrapers.core.models import Document


class VersionManager:
    @staticmethod
    def get_latest_version(documents: list[Document]) -> date | None:
        if not documents:
            return None

        same_versions: set[date] = set(documents.pop().versions.items())
        for document in documents:
            same_versions.intersection(document.versions.items())
        sorted(same_versions, reverse=True)
        return same_versions.pop() if same_versions else None