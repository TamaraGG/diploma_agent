import polars as pl

from database.base.enums import CurrencyType, DebtStatus, RegionLevel
from database.dataframe_base.base_processor import BaseDataframeProcessor
from database.debt_sme_subj.base_processor import BaseDebtSmeSubjProcessor
from exceptions import InvalidDataStructureError


class IDebtSmeSubjProcessor(BaseDebtSmeSubjProcessor):
    SHEET_MAPPING = {
        "ИП в рублях": (CurrencyType.RUB, DebtStatus.TOTAL),
        "ИП в т.ч. просроч. в рублях": (CurrencyType.RUB, DebtStatus.OVERDUE),
        "ИП в инвалюте": (CurrencyType.FX, DebtStatus.TOTAL),
        "ИП в т.ч. просроч. в инвалюте": (CurrencyType.FX, DebtStatus.OVERDUE),
        "ИП итого": (CurrencyType.TOTAL, DebtStatus.TOTAL),
        "ИП в т.ч.просроч.": (CurrencyType.TOTAL, DebtStatus.OVERDUE),
    }
