from datetime import date

from sqlalchemy import String, Float, Date, Enum as SQLEnum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database.base.base import Base
from database.base.enums import RegionLevel, CurrencyType, DebtStatus, EntityType


class ADebtCorp(Base):
    __tablename__ = "a_debt_corp"

    id: Mapped[int] = mapped_column(primary_key=True)

    report_date: Mapped[date] = mapped_column(Date, index=True)
    region_name: Mapped[str] = mapped_column(String, index=True)
    region_level: Mapped[RegionLevel] = mapped_column(SQLEnum(RegionLevel))

    currency: Mapped[CurrencyType] = mapped_column(SQLEnum(CurrencyType))
    debt_status: Mapped[DebtStatus] = mapped_column(SQLEnum(DebtStatus))

    activity_type: Mapped[str] = mapped_column(String(255), index=True)
    amount_mln_rub: Mapped[float] = mapped_column(Float)