from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: UUID
    knowledge_base_id: UUID
    original_filename: str
    file_type: str
    content_type: str | None
    file_size: int
    status: str
    chunk_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}


class IngestionJobResponse(BaseModel):
    id: UUID
    document_id: UUID
    celery_task_id: str | None
    status: str
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    job: IngestionJobResponse
