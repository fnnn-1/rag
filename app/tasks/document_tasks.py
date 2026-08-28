from datetime import datetime, timezone
import asyncio
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Document, IngestionJob
from app.parsers.document_parser import parse_document
from app.tasks.celery_app import celery_app


async def _process_document(document_id: str, job_id: str) -> dict:
    async with SessionLocal() as session:
        document = await session.scalar(select(Document).where(Document.id == document_id))
        job = await session.scalar(select(IngestionJob).where(IngestionJob.id == job_id))
        if document is None or job is None:
            raise ValueError("文档或处理任务不存在")

        now = datetime.now(timezone.utc)
        document.status = "processing"
        job.status = "processing"
        job.started_at = now
        await session.commit()

        try:
            parsed = parse_document(Path(document.storage_path))
            if not parsed.text or not parsed.chunks:
                raise ValueError("文档未解析出有效文本")

            document.extracted_text = parsed.text
            document.chunk_count = len(parsed.chunks)
            document.status = "completed"
            document.error_message = None
            document.processed_at = datetime.now(timezone.utc)
            job.status = "completed"
            job.error_message = None
            job.finished_at = datetime.now(timezone.utc)
            await session.commit()
            return {"document_id": str(document.id), "chunk_count": document.chunk_count, "status": "completed"}
        except Exception as exc:
            document.status = "failed"
            document.error_message = str(exc)[:2000]
            job.status = "failed"
            job.error_message = str(exc)[:2000]
            job.finished_at = datetime.now(timezone.utc)
            await session.commit()
            raise


@celery_app.task(
    bind=True,
    name="app.tasks.process_document",
    autoretry_for=(OSError, RuntimeError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 2},
)
def process_document(self, document_id: str, job_id: str) -> dict:
    return asyncio.run(_process_document(document_id, job_id))
