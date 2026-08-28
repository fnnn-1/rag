from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.api.knowledge_bases import get_owned_knowledge_base
from app.core.config import settings
from app.db.session import get_db
from app.models import Document, IngestionJob, User
from app.schemas.documents import DocumentResponse, DocumentUploadResponse, IngestionJobResponse
from app.tasks.document_tasks import process_document

router = APIRouter(tags=["documents"])
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".md", ".markdown", ".txt"}


async def get_owned_document(document_id: UUID, user: User, db: AsyncSession) -> Document:
    document = await db.scalar(
        select(Document)
        .join(Document.knowledge_base)
        .where(Document.id == document_id, Document.knowledge_base.has(owner_id=user.id))
    )
    if document is None:
        raise HTTPException(status_code=404, detail="文档不存在或无权访问")
    return document


@router.post(
    "/knowledge-bases/{knowledge_base_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    knowledge_base_id: UUID,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    knowledge_base = await get_owned_knowledge_base(knowledge_base_id, user, db)
    original_filename = Path(file.filename or "").name
    extension = Path(original_filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="仅支持 PDF、DOCX、Markdown 和 TXT 文件")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件内容不能为空")
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail=f"文件不能超过 {settings.max_upload_size_mb} MB")

    storage_dir = settings.ensure_upload_dir()
    storage_filename = f"{uuid4_str()}{extension}"
    storage_path = storage_dir / storage_filename
    storage_path.write_bytes(content)

    document = Document(
        knowledge_base_id=knowledge_base.id,
        original_filename=original_filename,
        storage_filename=storage_filename,
        storage_path=str(storage_path),
        file_type=extension.lstrip("."),
        content_type=file.content_type,
        file_size=len(content),
        status="queued",
    )
    db.add(document)
    await db.flush()
    job = IngestionJob(document_id=document.id, status="queued")
    db.add(job)
    await db.commit()
    await db.refresh(document)
    await db.refresh(job)

    try:
        task = process_document.delay(str(document.id), str(job.id))
        job.celery_task_id = task.id
        await db.commit()
        await db.refresh(job)
    except Exception as exc:
        document.status = "failed"
        document.error_message = f"任务提交失败：{exc}"
        job.status = "failed"
        job.error_message = document.error_message
        await db.commit()
        raise HTTPException(status_code=503, detail="文档处理任务提交失败，请稍后重试") from exc

    return DocumentUploadResponse(document=document, job=job)


def uuid4_str() -> str:
    import uuid

    return str(uuid.uuid4())


@router.get("/knowledge-bases/{knowledge_base_id}/documents", response_model=list[DocumentResponse])
async def list_documents(
    knowledge_base_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Document]:
    await get_owned_knowledge_base(knowledge_base_id, user, db)
    result = await db.scalars(
        select(Document)
        .where(Document.knowledge_base_id == knowledge_base_id)
        .order_by(Document.created_at.desc())
    )
    return list(result.all())


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Document:
    return await get_owned_document(document_id, user, db)


@router.get("/jobs/{job_id}", response_model=IngestionJobResponse)
async def get_ingestion_job(
    job_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IngestionJob:
    job = await db.scalar(
        select(IngestionJob)
        .join(IngestionJob.document)
        .where(IngestionJob.id == job_id, Document.knowledge_base.has(owner_id=user.id))
    )
    if job is None:
        raise HTTPException(status_code=404, detail="处理任务不存在或无权访问")
    return job


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document = await get_owned_document(document_id, user, db)
    storage_path = Path(document.storage_path)
    await db.delete(document)
    await db.commit()
    if storage_path.exists():
        storage_path.unlink()
