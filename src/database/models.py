import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SQLEnum, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from database.base import Base


class FileProcessingStatus(str, enum.Enum):
    DISCOVERED = "DISCOVERED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class ProcessedFile(Base):
    __tablename__ = "processed_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String, unique=True, index=True)
    file_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    etag: Mapped[str | None] = mapped_column(String)

    status: Mapped[FileProcessingStatus] = mapped_column(
        SQLEnum(FileProcessingStatus),
        default=FileProcessingStatus.DISCOVERED
    )

    load_date: Mapped[datetime | None] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    error_message: Mapped[str | None] = mapped_column(String)
