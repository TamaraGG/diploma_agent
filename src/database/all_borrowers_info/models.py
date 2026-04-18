from datetime import date

from sqlalchemy import String, Float, Date, Enum as SQLEnum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database.base.base import Base
from database.base.enums import RegionLevel, CurrencyType, DebtStatus, EntityType


class AllBorrowersInfo(Base):
    __tablename__ = "all_borrowers_info"

    id: Mapped[int] = mapped_column(primary_key=True)

    entity_type: Mapped[EntityType] = mapped_column(SQLEnum(EntityType, native_enum=True))
    metric_category: Mapped[str] = mapped_column(String(255))
    report_date: Mapped[date] = mapped_column(Date, index=True)
    value: Mapped[float] = mapped_column(Float)