import io

import polars as pl

from exceptions import SheetNotFoundError, InvalidFileFormatError, InvalidDataStructureError


class ObsAlgorithm4Processor:
    default_sheet_name: str = "Алгоритмы (табл.4)"
    @staticmethod
    def process(file_bytes: bytes, dataset_id: int, sheet_name: str = default_sheet_name) -> pl.DataFrame:

        try:
            raw_df = pl.read_excel(
                io.BytesIO(file_bytes),
                sheet_name=sheet_name,
                infer_schema_length=0
            )
        except ValueError as e:
            if "sheet" in str(e).lower() or "not found" in str(e).lower():
                raise SheetNotFoundError(f"В файле отсутствует лист с названием '{sheet_name}'.")
            raise InvalidFileFormatError(f"Ошибка чтения Excel: {str(e)}")
        except Exception as e:
            raise InvalidFileFormatError(f"Файл поврежден или не является Excel-таблицей. Ошибка: {e}")

        if len(raw_df.columns) < 3:
            raise InvalidDataStructureError(
                f"Неверный формат таблицы. Ожидается минимум 3 колонки, найдено: {len(raw_df.columns)}"
            )


        df = raw_df.rename({
            raw_df.columns[0]: "code",
            raw_df.columns[1]: "name",
            raw_df.columns[2]: "formula"
        })

        df = df.with_columns([
            pl.col("code").cast(pl.Utf8).str.strip_chars().replace("", None),
            pl.col("name").cast(pl.Utf8).str.strip_chars(),
            pl.col("formula").cast(pl.Utf8).str.strip_chars().replace("", None)
        ]).filter(pl.col("name").is_not_null())

        if df.is_empty():
            raise InvalidDataStructureError("После очистки файла не найдено ни одной значащей строки.")

        df = df.with_columns([
            pl.lit(dataset_id).alias("dataset_id"),
            pl.when(pl.col("code").is_null()).then(0)
            .otherwise(pl.col("code").str.count_matches(r"\.") + 1)
            .alias("hierarchy_level"),
            pl.when(pl.col("formula").is_null() | pl.col("code").is_null())
            .then(True).otherwise(False).alias("is_group")
        ])

        return df
