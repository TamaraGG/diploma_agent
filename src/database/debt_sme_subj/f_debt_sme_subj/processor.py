import polars as pl

from database.base.enums import CurrencyType, DebtStatus, RegionLevel
from database.dataframe_base.base_processor import BaseDataframeProcessor
from database.debt_sme_subj.base_processor import BaseDebtSmeSubjProcessor
from exceptions import InvalidDataStructureError


class FDebtSmeSubjProcessor(BaseDebtSmeSubjProcessor):
    SHEET_MAPPING = {
        "МСП в рублях": (CurrencyType.RUB, DebtStatus.TOTAL),
        "МСП в т.ч. проср в рублях": (CurrencyType.RUB, DebtStatus.OVERDUE),
        "МСП в инвалюте": (CurrencyType.FX, DebtStatus.TOTAL),
        "МСП в т.ч. просроч. в инвалюте": (CurrencyType.FX, DebtStatus.OVERDUE),
        "МСП Итого": (CurrencyType.TOTAL, DebtStatus.TOTAL),
        "МСП в т.ч. просроч.": (CurrencyType.TOTAL, DebtStatus.OVERDUE),
    }
