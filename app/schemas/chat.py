from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    knowledge_base_id: UUID
    question: str = Field(min_length=1, max_length=4000)
    conversation_id: UUID | None = None
    top_k: int = Field(default=5, ge=1, le=10)


class CitationResponse(BaseModel):
    citation_index: int
    document_id: UUID
    document_name: str
    chunk_id: UUID
    content: str
    page_number: int | None
    section: str | None
    rerank_score: float


class ChatResponse(BaseModel):
    answer: str
    grounded: bool
    conversation_id: UUID
    message_id: UUID
    trace_id: str
    citations: list[CitationResponse]
    retrieval_latency_ms: int
    generation_latency_ms: int
    llm_provider: str


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    grounded: bool
    created_at: datetime

    model_config = {"from_attributes": True}
