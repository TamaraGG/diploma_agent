import polars as pl
from dataclasses import dataclass
from database.dataframe_base.base_processor import BaseDataframeProcessor


@dataclass
class ProcessedFinancialData:
    actives_df: pl.DataFrame
    percents_df: pl.DataFrame | None


class BaseObsProcessor(BaseDataframeProcessor):

    @staticmethod
    def _filter_actives_section(df: pl.DataFrame) -> pl.DataFrame:
        start_marks = df.with_row_index().filter(pl.col("code").str.contains("(?i)^Активы")).select("index")
        start_idx = start_marks.item(0, 0) if not start_marks.is_empty() else 0

        end_marks = df.with_row_index().filter(
            pl.col("code").str.contains("(?i)Итого активов|(?i)^Обязательства|(?i)^Пассивы")).select("index")
        end_idx = end_marks.item(0, 0) if not end_marks.is_empty() else df.height

        return df.slice(start_idx, end_idx - start_idx)

    @staticmethod
    def _fix_missing_codes(df: pl.DataFrame) -> pl.DataFrame:
        df = df.with_columns(parent_code=pl.col("code").fill_null(strategy="forward"))
        df = df.with_columns(is_null_code=pl.col("code").is_null()).with_columns(
            null_index=pl.col("is_null_code").cum_sum().over("parent_code")
        )
        df = df.with_columns(
            code=pl.when(pl.col("code").is_null() & pl.col("parent_code").is_not_null())
            .then(pl.format("{}.v{}", pl.col("parent_code"), pl.col("null_index")))
            .otherwise(pl.col("code"))
        )
        return df.drop(["parent_code", "is_null_code", "null_index"])