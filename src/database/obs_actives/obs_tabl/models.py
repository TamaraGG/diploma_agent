from datetime import date

from sqlalchemy import String, Date, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Enum as SQLEnum, func, Text

from database.base.base import Base
from database.base.enums import CurrencyType
from database.obs_actives.base_models import ObsActivesMixin


class ObsTabl(Base, ObsActivesMixin):
    __tablename__ = "obs_tabl"

