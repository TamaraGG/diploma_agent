from abc import ABC, abstractmethod


class BaseWebFileLoader(ABC):
    @staticmethod
    @abstractmethod
    def load_file(url: str, folder_path: str, file_name: str | None = None) -> bool:
        pass