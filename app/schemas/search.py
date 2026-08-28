from uuid import UUID

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=50)


class SearchResultResponse(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_name: str
    content: str
    page_number: int | None
    section: str | None
    vector_score: float | None
    keyword_score: float | None
    hybrid_score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultResponse]
    embedding_provider: str
    result_count: int
