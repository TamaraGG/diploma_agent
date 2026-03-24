import yaml
from pydantic import ValidationError
from yaml import SafeLoader

from src.file_loading.models.models import WebPage


def get_web_pages(config_path: str) -> list[WebPage]:
    pages_list: list[WebPage] =[]
    with open(config_path, 'r', encoding='utf-8') as f:
        yaml_data = list(yaml.load_all(f, Loader=SafeLoader))
        for data in yaml_data:
            try:
                obj = WebPage(**data)
                pages_list.append(obj)
            except ValidationError as e:
                print(f"Не получилось создать объект WebPage из \n{data}\nошибка:\n{e}")
    return pages_list