from sqlalchemy import String, Date, Float, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, declarative_mixin
from database.base.base import Base
from database.base.enums import CurrencyType
from datetime import date

@declarative_mixin
class ObsActivesMixin:

    id: Mapped[int] = mapped_column(primary_key=True)
    indicator_code: Mapped[str | None] = mapped_column(String(50), index=True)
    indicator_name: Mapped[str] = mapped_column(String)
    report_date: Mapped[date] = mapped_column(Date, index=True)
    currency_type: Mapped[CurrencyType] = mapped_column(SQLEnum(CurrencyType), index=True)
    value: Mapped[float | None] = mapped_column(Float)

class FinancialReportPercent(Base):
    __tablename__ = "financial_report_percents"
    id: Mapped[int] = mapped_column(primary_key=True)
    indicator_code: Mapped[str | None] = mapped_column(String(50))
    percent_value: Mapped[float | None] = mapped_column(Float)