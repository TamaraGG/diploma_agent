from datetime import datetime

from src.file_loading.models.models import Document, DocumentVersion
from src.file_loading.version_manager.base_version_manager import BaseVersionManager


class VersionManager(BaseVersionManager):
    @staticmethod
    def get_latest_version(documents: list[Document]) -> list[DocumentVersion] | None:
        if not documents:
            return None

        return [doc.versions[0] for doc in documents]

    @staticmethod
    def get_last_common_month(documents: list[Document]) -> list[DocumentVersion]:
        if not documents:
            return []

        date_sets = [{datetime(dd.load_date.year, dd.load_date.month, 1)
                      for dd in doc.versions}
                      for doc in documents]
        common_month = date_sets[0]
        for ds in date_sets:
            common_month = common_month.intersection(ds)
            if not common_month:
                break

        target_date = sorted(list(common_month), reverse=True)[0]

        doc_versions = []
        for document in documents:
            v = [version for version in document.versions
                 if datetime(version.load_date.year, version.load_date.month, 1) == target_date]
            doc_versions.append(v[-1] if v else None)
        return doc_versions