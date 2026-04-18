from datetime import date
from sqlalchemy import String, Date, Float, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, declarative_mixin

from database.base.enums import RegionLevel, CurrencyType, DebtStatus


@declarative_mixin
class DebtSubjMixin:
    id: Mapped[int] = mapped_column(primary_key=True)

    region_name: Mapped[str] = mapped_column(String, index=True)
    region_level: Mapped[RegionLevel] = mapped_column(SQLEnum(RegionLevel))

    report_date: Mapped[date] = mapped_column(Date, index=True)

    currency: Mapped[CurrencyType] = mapped_column(SQLEnum(CurrencyType), index=True)
    debt_status: Mapped[DebtStatus] = mapped_column(SQLEnum(DebtStatus), index=True)

    amount_mln_rub: Mapped[float | None] = mapped_column(Float)
