from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import Text

from database.base.base import Base


class OBSAlgorithm4(Base):
    __tablename__ = "obs_algorithms_4"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str | None] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    formula: Mapped[str | None] = mapped_column(Text)
    hierarchy_level: Mapped[int] = mapped_column(default=0)
    is_group: Mapped[bool] = mapped_column(default=False)

