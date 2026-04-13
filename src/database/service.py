from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from data_files_loading.models.models import DocumentVersion
from database.base import connection
from database.dao import ProcessedFileDAO
from database.models import FileProcessingStatus


class ProcessedFileService:
    @classmethod
    @connection
    async def get_by_url(cls, url: str, session: AsyncSession = None) -> Optional[DocumentVersion]:
        record = await ProcessedFileDAO.find_one_or_none(session, url=url)
        if not record:
            return None

        # Конвертируем SQLAlchemy модель в Pydantic
        # Так как в БД нет поля name, мы вытягиваем его из URL на лету
        return DocumentVersion.model_validate(
            record,
            update={"name": url.split('/')[-1]}
        )

    @classmethod
    @connection
    async def start_processing(cls, url: str, session: AsyncSession = None) -> None:
        """Помечает файл как 'В ПРОЦЕССЕ'."""
        record = await ProcessedFileDAO.find_one_or_none(session, url=url)

        if not record:
            await ProcessedFileDAO.add(
                session,
                url=url,
                status=FileProcessingStatus.PROCESSING
            )
        else:
            record.status = FileProcessingStatus.PROCESSING
            record.error_message = None
            await session.commit()

    @classmethod
    @connection
    async def mark_as_processed(cls, document: DocumentVersion, session: AsyncSession = None) -> DocumentVersion:
        """
        Сохраняет успешный результат обработки.
        Принимает Pydantic модель с новыми данными (хеш, etag) и сохраняет в БД.
        """
        record = await ProcessedFileDAO.find_one_or_none(session, url=document.url)

        if not record:
            await ProcessedFileDAO.add(
                session,
                url=document.url,
                file_hash=document.file_hash,
                etag=document.etag,
                load_date=document.load_date,
                status=FileProcessingStatus.PROCESSED
            )
        else:
            record.file_hash = document.file_hash
            record.etag = document.etag
            record.load_date = document.load_date
            record.status = FileProcessingStatus.PROCESSED
            record.error_message = None
            await session.commit()

        # Обновляем статус в самой Pydantic модели и возвращаем ее
        document.status = FileProcessingStatus.PROCESSED
        return document

    @classmethod
    @connection
    async def mark_as_failed(cls, url: str, error_msg: str, session: AsyncSession = None) -> None:
        """Записывает ошибку в БД."""
        record = await ProcessedFileDAO.find_one_or_none(session, url=url)

        if not record:
            await ProcessedFileDAO.add(
                session,
                url=url,
                status=FileProcessingStatus.FAILED,
                error_message=error_msg
            )
        else:
            record.status = FileProcessingStatus.FAILED
            record.error_message = error_msg
            await session.commit()