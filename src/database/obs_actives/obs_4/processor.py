from dataclasses import dataclass
from datetime import datetime
import io

import polars as pl

from database.dataframe_base.base_processor import BaseDataframeProcessor
from database.obs_actives.base_processor import BaseObsProcessor, ProcessedFinancialData
from exceptions import SheetNotFoundError, InvalidFileFormatError, InvalidDataStructureError


class ObsActivesProcessor(BaseObsProcessor):
    default_sheet_name: str = "4"

    actives_df: pl.DataFrame
    percents_df: pl.DataFrame | None

    CURRENCY_MAP = {
        "рубли": "RUB",
        "валюта": "VAL",
        "всего": "TOTAL"
    }

    @classmethod
    def process(cls, file_bytes: bytes, dataset_id: int, sheet_name: str = default_sheet_name) -> ProcessedFinancialData:
        raw_df: pl.DataFrame = cls._check_bytes(file_bytes, sheet_name)

        cls._check_df_length(raw_df, 4)

        row_dates = raw_df.row(1)
        row_curs = raw_df.row(2)

        col_names = ["code", "name"]
        value_columns = []
        percent_col_name = None

        current_date = None

        for i in range(2, len(row_dates)):
            date_val = str(row_dates[i]).strip() if row_dates[i] else "null"
            cur_val = str(row_curs[i]).strip().lower() if row_curs[i] else "null"

            if "в %" in date_val.lower() or "в %" in cur_val.lower():
                percent_col_name = f"col_{i}_percent"
                col_names.append(percent_col_name)
                continue

            if date_val != "null" and date_val != "none":
                parsed_date = cls._parse_date(date_val)
                if parsed_date:
                    current_date = parsed_date

            if current_date and cur_val in cls.CURRENCY_MAP:
                cur_enum = cls.CURRENCY_MAP[cur_val]
                new_col_name = f"{current_date}_{cur_enum}"
                col_names.append(new_col_name)
                value_columns.append(new_col_name)
            else:
                col_names.append(f"ignore_{i}")

        if len(col_names) != len(raw_df.columns):
            raise InvalidDataStructureError("Ошибка разбора структуры колонок")

        df = raw_df.rename(dict(zip(raw_df.columns, col_names)))

        df = cls._filter_actives_section(df)
        df = cls._fix_missing_codes(df)

        df = df.slice(3).select([c for c in df.columns if not c.startswith("ignore_")])

        df = df.with_columns([
            pl.col("code").cast(pl.Utf8).str.strip_chars().replace({"None": None, "": None}),
            pl.col("name").cast(pl.Utf8).str.strip_chars()
        ]).filter(pl.col("name").is_not_null())

        cols_to_clean = value_columns.copy()
        if percent_col_name: cols_to_clean.append(percent_col_name)
        df = df.with_columns([cls._clean_numeric(c) for c in cols_to_clean])

        actives_df = df.unpivot(
            index=["code", "name"],
            on=value_columns,
            variable_name="meta",
            value_name="value"
        )

        actives_df = actives_df.with_columns([
            pl.col("meta").str.split("_").list.get(0).cast(pl.Date).alias("report_date"),
            pl.col("meta").str.split("_").list.get(1).alias("currency_type")
        ]).drop("meta")

        actives_df = actives_df.rename({
            "code": "indicator_code",
            "name": "indicator_name"
        })

        percents_df = None
        if percent_col_name:
            percents_df = df.select([
                pl.col("code").alias("indicator_code"),
                pl.col(percent_col_name).alias("percent_value")
            ]).filter(pl.col("percent_value").is_not_null())

        return ProcessedFinancialData(
            actives_df=actives_df,
            percents_df=percents_df
        )
