from database.obs_actives.base_processor import BaseObsProcessor, ProcessedFinancialData
import polars as pl

from exceptions import InvalidDataStructureError


class ObsActivesSplitProcessor(BaseObsProcessor):
    default_sheet_name = "Активы - рубли"

    SHEET_MAPPING = {
        "Активы - рубли": "RUB",
        "Активы - валюта": "FX",
        "Активы - всего": "TOTAL",
    }

    @classmethod
    def process(cls, file_bytes: bytes, dataset_id: int, sheet_name: str = default_sheet_name) -> ProcessedFinancialData:

        sheet_name_clean = sheet_name.strip()
        currency_val = None
        for key, val in cls.SHEET_MAPPING.items():
            if key.lower() in sheet_name_clean.lower():
                currency_val = val
                break

        if not currency_val:
            raise InvalidDataStructureError(f"Неизвестный лист: {sheet_name}. Невозможно определить валюту.")

        raw_df = cls._check_bytes(file_bytes, sheet_name)
        cls._check_df_length(raw_df, 5)

        header_row_idx = -1
        code_col_idx = -1
        name_col_idx = -1

        for idx, row in enumerate(raw_df.iter_rows()):
            row_str = [str(cell).lower().strip() if cell else "" for cell in row]

            if "показатель" in row_str or "показатель (млрд руб.)" in row_str:
                header_row_idx = idx
                for col_idx, cell_val in enumerate(row_str):
                    if "№ п.п" in cell_val:
                        code_col_idx = col_idx
                    elif "показатель" in cell_val:
                        name_col_idx = col_idx
                break

        if header_row_idx == -1 or name_col_idx == -1:
            raise InvalidDataStructureError("Не удалось найти строку с заголовками ('Показатель').")

        header_row = raw_df.row(header_row_idx)
        col_rename_map = {
            raw_df.columns[code_col_idx]: "code",
            raw_df.columns[name_col_idx]: "name"
        }

        value_columns = []

        for i in range(name_col_idx + 1, len(header_row)):
            cell_val = str(header_row[i]).strip() if header_row[i] else ""
            parsed_date = cls._parse_date(cell_val)

            if parsed_date:
                col_name = f"date_{parsed_date}"
                col_rename_map[raw_df.columns[i]] = col_name
                value_columns.append(col_name)
            else:
                col_rename_map[raw_df.columns[i]] = f"ignore_{i}"

        df = raw_df.rename(col_rename_map)
        df = df.slice(header_row_idx + 1)

        cols_to_keep = ["code", "name"] + value_columns
        df = df.select([c for c in cols_to_keep if c in df.columns])

        df = cls._filter_actives_section(df)
        df = cls._fix_missing_codes(df)

        df = df.with_columns([
            pl.col("code").cast(pl.Utf8).str.strip_chars().replace({"None": None, "": None, "null": None}),
            pl.col("name").cast(pl.Utf8).str.strip_chars()
        ]).filter(pl.col("name").is_not_null() & (pl.col("name") != ""))

        df = df.with_columns([cls._clean_numeric(c) for c in value_columns])

        actives_df = df.unpivot(
            index=["code", "name"],
            on=value_columns,
            variable_name="raw_date",
            value_name="value"
        )

        actives_df = actives_df.with_columns([
            pl.col("raw_date").str.replace("date_", "").cast(pl.Date).alias("report_date"),
            pl.lit(currency_val.value if hasattr(currency_val, 'value') else currency_val).alias("currency_type")
        ]).drop("raw_date")

        actives_df = actives_df.rename({
            "code": "indicator_code",
            "name": "indicator_name"
        })

        return ProcessedFinancialData(
            actives_df=actives_df,
            percents_df=None
        )