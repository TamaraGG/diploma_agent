from typing import Any, Self

from pydantic import BaseModel, field_validator, Field
from datetime import date, datetime


def find_all_paths(data: str | list[str] | dict[str, str | dict | list]) -> list[list[str]]:
    if isinstance(data, str):
        return [[data]]

    if isinstance(data, list):
        all_paths = []
        for item in data:
            all_paths.extend(find_all_paths(item))
        return all_paths

    if isinstance(data, dict):
        all_paths = []
        for key, value in data.items():
            sub_paths = find_all_paths(value)
            for p in sub_paths:
                all_paths.append([key] + p)
        return all_paths

    return []


class WebPage(BaseModel):
    name: str
    url: str
    paths: list[list[str]] = Field(default_factory=list)

    @field_validator("paths", mode="before")
    @classmethod
    def validate_paths(cls, value: Any) -> Any:
        if isinstance(value, (str, dict, list)):
            value = find_all_paths(value)
        return value


class Document(BaseModel):
    name: str
    load_date: datetime | None = None
    url: str


class DocumentVersion(BaseModel):
    name: str = Field(description="Название документа")
    versions: dict[datetime, list[str]] = Field(description="Словарь со всеми версиями документа по датам")

    @field_validator("versions", mode="before")
    @classmethod
    def sort_versions(cls, value: Any) -> Any:
        if isinstance(value, dict):
            sorted(value)
        return value
