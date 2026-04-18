import re
from typing import Any

import polars as pl

from database.base.enums import EntityType
from database.dataframe_base.base_processor import BaseDataframeProcessor
from exceptions import InvalidDataStructureError


class AllBorrowersInfoProcessor(BaseDataframeProcessor):
    default_sheet_name = "Данные"

    ENTITY_MAPPING = {
        "всего, в том числе:": "TOTAL",
        "юридические лица": "LEGAL_ENTITY",
        "индивидуальные предприниматели": "INDIVIDUAL"
    }

    RU_MONTHS = {
        "январь": "01", "февраль": "02", "март": "03", "апрель": "04",
        "май": "05", "июнь": "06", "июль": "07", "август": "08",
        "сентябрь": "09", "октябрь": "10", "ноябрь": "11", "декабрь": "12"
    }

    @classmethod
    def _parse_mixed_date(cls, text: str) -> str | None:
        if not text: return None
        text_str = str(text).strip().lower()

        parsed = cls._parse_date(text_str)
        if parsed: return parsed

        match = re.search(r'([а-я]+)\s+(\d{4})', text_str)
        if match:
            month_word, year = match.groups()
            if month_word in cls.RU_MONTHS:
                month_num = cls.RU_MONTHS[month_word]
                return f"{year}-{month_num}-01"
        return None

    @staticmethod
    def _clean_val_python(val: Any) -> float | None:
        if val is None: return None
        s = str(val).strip().replace(" ", "").replace("\xa0", "")
        if not s or s.lower() in ["x", "-", "null", "none"]:
            return None
        try:
            return float(s)
        except ValueError:
            return None

    @classmethod
    def process(cls, file_bytes: bytes, dataset_id: int, sheet_name: str = default_sheet_name) -> pl.DataFrame:
        raw_df = cls._check_bytes(file_bytes, sheet_name)
        cls._check_df_length(raw_df, 5)

        records = []

        current_main_category = ""
        current_sub_category = ""

        is_last_text = False

        current_dates = []

        for row in raw_df.iter_rows():
            col0 = str(row[0]).strip() if row[0] else ""
            col0_lower = col0.lower()

            entity_type = None
            for key, enum_val in cls.ENTITY_MAPPING.items():
                if key in col0_lower:
                    entity_type = enum_val
                    break

            if entity_type:

                final_metric_category = " | ".join([current_main_category, current_sub_category])

                for i, val in enumerate(row[1:]):
                    if i < len(current_dates) and current_dates[i] is not None:
                        cleaned_val = cls._clean_val_python(val)
                        if cleaned_val is not None:
                            records.append({
                                "entity_type": entity_type,
                                "metric_category": final_metric_category,
                                "report_date": current_dates[i],
                                "value": cleaned_val
                            })
                is_last_text = False
                continue

            dates_found = []
            for cell in row[1:]:
                dates_found.append(cls._parse_mixed_date(cell))

            if any(dates_found):
                current_dates = dates_found

            if col0:

                if re.match(r'^\d+\.', col0) and not is_last_text:
                    current_main_category = col0
                else:
                    if is_last_text:
                        current_sub_category += col0
                    else:
                        current_sub_category = col0
                is_last_text = False


        if not records:
            raise InvalidDataStructureError("Не удалось извлечь данные.")

        df = pl.DataFrame(records, schema={
            "entity_type": pl.Utf8,
            "metric_category": pl.Utf8,
            "report_date": pl.Utf8,
            "value": pl.Float64
        })

        df = df.with_columns(
            pl.col("report_date").cast(pl.Date)
        )

        return df
