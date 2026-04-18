import re
from datetime import date, datetime
import polars as pl

from database.base.enums import CurrencyType, DebtStatus, RegionLevel
from database.dataframe_base.base_processor import BaseDataframeProcessor
from exceptions import InvalidDataStructureError


class ADebtCorpProcessor(BaseDataframeProcessor):
    default_sheet_name = "в рублях"
    SHEET_MAPPING = {
        "врублях": (CurrencyType.RUB, DebtStatus.TOTAL),
        "вт.ч.просроч.врублях": (CurrencyType.RUB, DebtStatus.OVERDUE),
        "винвалюте": (CurrencyType.FX, DebtStatus.TOTAL),
        "вт.ч.просроч.винвалюте": (CurrencyType.FX, DebtStatus.OVERDUE),
        "итого": (CurrencyType.TOTAL, DebtStatus.TOTAL),
    }

    @staticmethod
    def _normalize_sheet_name(name: str) -> str:
        return name.lower().replace(" ", "").strip()

    @classmethod
    def _extract_date_from_header(cls, raw_df: pl.DataFrame) -> str | None:
        """Ищет дату в первых 10 строках первой колонки с помощью регулярки"""
        for cell in raw_df.head(10).get_column(raw_df.columns[0]).to_list():
            if isinstance(cell, str):
                match = re.search(r"(\d{2}\.\d{2}\.\d{4})", cell)
                if match:
                    return cls._parse_date(match.group(1))
        return None

    @classmethod
    def process(cls, file_bytes: bytes, dataset_id: int, sheet_name: str = default_sheet_name) -> pl.DataFrame:
        norm_sheet = cls._normalize_sheet_name(sheet_name)

        if norm_sheet not in cls.SHEET_MAPPING:
            raise InvalidDataStructureError(
                f"Неизвестный лист: '{sheet_name}'. "
                f"Ожидается один из: 'в рублях', 'в инвалюте', 'итого' и т.д."
            )

        currency_val, status_val = cls.SHEET_MAPPING[norm_sheet]

        raw_df = cls._check_bytes(file_bytes, sheet_name)
        cls._check_df_length(raw_df, 5)

        report_date = cls._extract_date_from_header(raw_df)
        if not report_date:
            raise InvalidDataStructureError(f"Не удалось найти дату отчета на листе '{sheet_name}'.")

        start_marks = raw_df.with_row_index().filter(
            pl.col(raw_df.columns[0]).cast(pl.Utf8).str.to_uppercase().str.contains("РОССИЙСКАЯ ФЕДЕРАЦИЯ")
        )

        if start_marks.is_empty():
            raise InvalidDataStructureError("Не найдена стартовая строка 'РОССИЙСКАЯ ФЕДЕРАЦИЯ'.")

        data_start_idx = start_marks.item(0, "index")

        header_row = raw_df.row(data_start_idx - 1)

        col_rename_map = {raw_df.columns[0]: "region_name"}
        activity_columns = []

        for i in range(1, len(header_row)):
            col_name = str(header_row[i]).strip() if header_row[i] else ""

            col_name = re.sub(r'[\n_]+', ' ', col_name)
            col_name = re.sub(r'\s+', ' ', col_name).strip()

            if not col_name or col_name.lower() in ['none', 'null']:
                col_name = f"unknown_activity_{i}"

            if col_name in col_rename_map.values():
                col_name = f"{col_name}_{i}"

            col_rename_map[raw_df.columns[i]] = col_name
            activity_columns.append(col_name)

        df = raw_df.rename(col_rename_map)

        df = df.slice(data_start_idx).select(["region_name"] + activity_columns)

        df = df.with_columns(
            pl.col("region_name").cast(pl.Utf8).str.strip_chars()
        ).filter(
            pl.col("region_name").is_not_null() & (pl.col("region_name") != "")
        )

        df = df.with_columns([cls._clean_numeric(c) for c in activity_columns])

        df = df.unpivot(
            index=["region_name"],
            on=activity_columns,
            variable_name="activity_type",
            value_name="amount_mln_rub"
        )

        df = df.filter(~pl.col("activity_type").str.starts_with("unknown_activity"))

        df = df.with_columns([
            pl.when(pl.col("region_name").str.to_uppercase() == "РОССИЙСКАЯ ФЕДЕРАЦИЯ")
            .then(pl.lit(RegionLevel.COUNTRY.value))

            .when(pl.col("region_name").str.to_uppercase().str.ends_with("ФЕДЕРАЛЬНЫЙ ОКРУГ"))
            .then(pl.lit(RegionLevel.DISTRICT.value))

            .when(pl.col("region_name").str.to_lowercase().str.contains("в том числе|без данных"))
            .then(pl.lit(RegionLevel.SUB_REGION.value))

            .otherwise(pl.lit(RegionLevel.REGION.value))
            .cast(pl.Int32)
            .alias("region_level")
        ])

        df = df.with_columns([
            pl.lit(report_date).cast(pl.Date).alias("report_date"),
            pl.lit(currency_val.value).alias("currency"),
            pl.lit(status_val.value).alias("debt_status"),
        ])

        df = df.drop_nulls(subset=["amount_mln_rub"])

        return df
