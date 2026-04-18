from dataclasses import dataclass
from datetime import datetime
import io
from typing import Any

import polars as pl

from exceptions import SheetNotFoundError, InvalidFileFormatError, InvalidDataStructureError


class BaseDataframeProcessor:
    default_sheet_name: str = "Лист1"

    @staticmethod
    def _parse_date(date_str: str) -> str | None:
        if not date_str or date_str.lower() in ["none", "null", "nan"]:
            return None

        date_str = date_str.strip()

        if "-" in date_str:
            try:
                return date_str[:10]
            except Exception:
                pass

        if "." in date_str:
            try:
                return datetime.strptime(date_str, "%d.%m.%y").strftime("%Y-%m-%d")
            except ValueError:
                try:
                    return datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
                except ValueError:
                    pass
        return None

    @classmethod
    def _check_bytes(cls, file_bytes: bytes, sheet_name: str) -> pl.DataFrame:
        try:
            read_kwargs = {}
            if isinstance(sheet_name, int):
                read_kwargs["sheet_id"] = sheet_name
            else:
                read_kwargs["sheet_name"] = sheet_name

            raw_df = pl.read_excel(
                io.BytesIO(file_bytes),
                has_header=False,
                infer_schema_length=0,
                **read_kwargs
            )
        except Exception as e:
            if "not found" in str(e).lower():
                raise SheetNotFoundError(f"Лист '{sheet_name}' не найден в файле.")
            raise InvalidFileFormatError(f"Ошибка чтения Excel: {e}")

        return raw_df

    @classmethod
    def _check_df_length(cls, df: pl.DataFrame, rows_num: int):
        if df.height < rows_num:
            raise InvalidDataStructureError("Файл слишком короткий, не найдена структура данных.")

    @classmethod
    def process(cls, file_bytes: bytes, dataset_id: int, sheet_name: str = default_sheet_name) -> Any:
        pass

    @staticmethod
    def _clean_numeric(col_name: str):
        return (
            pl.col(col_name)
            .cast(pl.Utf8)
            .str.replace_all(r"\s+", "")  # Удаляем все пробелы
            .replace({"x": None, "None": None, "null": None, "": None})
            .cast(pl.Float64, strict=False)  # Безопасный каст в float
        )
