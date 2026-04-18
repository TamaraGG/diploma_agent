from database.base.enums import RegionLevel
from database.dataframe_base.base_processor import BaseDataframeProcessor
from exceptions import InvalidDataStructureError
import polars as pl

class BaseDebtSmeSubjProcessor(BaseDataframeProcessor):
    """
    Универсальный процессор для отчетов в разрезе Регионов и Дат.
    Наследники должны определить словарь SHEET_MAPPING.
    """
    default_sheet_name = 1
    SHEET_MAPPING: dict = {}

    @classmethod
    def process(cls, file_bytes: bytes, dataset_id: int, sheet_name: str = default_sheet_name) -> pl.DataFrame:
        sheet_name_clean = sheet_name.strip()

        mapping_key = next((k for k in cls.SHEET_MAPPING.keys() if k.lower() == sheet_name_clean.lower()), None)

        if not mapping_key:
            raise InvalidDataStructureError(
                f"Неизвестное название листа: '{sheet_name}'. "
                f"Ожидается одно из: {', '.join(cls.SHEET_MAPPING.keys())}"
            )

        currency_val, status_val = cls.SHEET_MAPPING[mapping_key]

        raw_df = cls._check_bytes(file_bytes, sheet_name)
        cls._check_df_length(raw_df, 4)

        date_row = raw_df.row(1)
        col_rename_map = {raw_df.columns[0]: "region_name"}
        value_columns = []

        for i in range(1, len(date_row)):
            cell_value = str(date_row[i]).strip() if date_row[i] else ""
            parsed_date = cls._parse_date(cell_value)

            if parsed_date:
                new_col_name = f"date_{parsed_date}"
                col_rename_map[raw_df.columns[i]] = new_col_name
                value_columns.append(new_col_name)
            else:
                col_rename_map[raw_df.columns[i]] = f"ignore_{i}"

        df = raw_df.rename(col_rename_map)
        cols_to_keep = ["region_name"] + value_columns
        df = df.slice(2).select(cols_to_keep)

        df = df.with_columns(
            pl.col("region_name").cast(pl.Utf8).str.strip_chars()
        ).filter(
            pl.col("region_name").is_not_null() & (pl.col("region_name") != "")
        )

        df = df.with_columns([cls._clean_numeric(c) for c in value_columns])

        df = df.unpivot(
            index=["region_name"],
            on=value_columns,
            variable_name="raw_date",
            value_name="amount_mln_rub"
        )

        df = df.with_columns(
            pl.col("raw_date").str.replace("date_", "").cast(pl.Date).alias("report_date")
        ).drop("raw_date")

        df = df.with_columns([
            pl.when(pl.col("region_name").str.to_uppercase() == "РОССИЙСКАЯ ФЕДЕРАЦИЯ")
            .then(pl.lit(RegionLevel.COUNTRY.value))
            .when(pl.col("region_name").str.to_uppercase().str.ends_with("ФЕДЕРАЛЬНЫЙ ОКРУГ"))
            .then(pl.lit(RegionLevel.DISTRICT.value))
            .otherwise(pl.lit(RegionLevel.REGION.value))
            .cast(pl.Int32)
            .alias("region_level"),

            pl.lit(currency_val.value).alias("currency"),
            pl.lit(status_val.value).alias("debt_status"),
            pl.lit(dataset_id).alias("dataset_id")  # Добавляем связь с метаданными
        ])

        return df.drop_nulls(subset=["amount_mln_rub"])