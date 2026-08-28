from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.llm.embeddings import get_embedding_provider
from app.models import Document, DocumentChunk


@dataclass(slots=True)
class SearchResult:
    chunk_id: UUID
    document_id: UUID
    document_name: str
    content: str
    page_number: int | None
    section: str | None
    vector_score: float | None
    keyword_score: float | None
    hybrid_score: float


async def vector_search(db: AsyncSession, knowledge_base_id: UUID, query_vector: list[float], limit: int):
    distance = DocumentChunk.embedding.cosine_distance(query_vector)
    statement = (
        select(DocumentChunk, Document, (1 - distance).label("score"))
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(Document.knowledge_base_id == knowledge_base_id, DocumentChunk.embedding.is_not(None))
        .order_by(distance)
        .limit(limit)
    )
    rows = (await db.execute(statement)).all()
    return [(chunk, document, float(score or 0.0)) for chunk, document, score in rows]


async def keyword_search(db: AsyncSession, knowledge_base_id: UUID, query: str, limit: int):
    ts_query = func.plainto_tsquery("simple", query.strip())
    rank = func.ts_rank_cd(DocumentChunk.search_vector, ts_query)
    statement = (
        select(DocumentChunk, Document, rank.label("score"))
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            Document.knowledge_base_id == knowledge_base_id,
            DocumentChunk.search_vector.op("@@")(ts_query),
        )
        .order_by(rank.desc())
        .limit(limit)
    )
    rows = (await db.execute(statement)).all()
    return [(chunk, document, float(score or 0.0)) for chunk, document, score in rows]


async def hybrid_search(
    db: AsyncSession,
    knowledge_base_id: UUID,
    query: str,
    top_k: int = 5,
) -> tuple[list[SearchResult], str]:
    if not query.strip():
        return [], "empty-query"
    top_k = max(1, min(top_k, 50))
    candidate_limit = max(top_k, settings.retrieval_candidate_k)
    provider = get_embedding_provider()
    query_vector = await provider.embed_query(query)
    vector_rows = await vector_search(db, knowledge_base_id, query_vector, candidate_limit)
    keyword_rows = await keyword_search(db, knowledge_base_id, query, candidate_limit)

    fused: dict[UUID, SearchResult] = {}
    vector_by_id = {chunk.id: score for chunk, _, score in vector_rows}
    keyword_by_id = {chunk.id: score for chunk, _, score in keyword_rows}
    for rank, (chunk, document, _) in enumerate(vector_rows, start=1):
        fused[chunk.id] = SearchResult(
            chunk_id=chunk.id,
            document_id=document.id,
            document_name=document.original_filename,
            content=chunk.content,
            page_number=chunk.page_number,
            section=chunk.section,
            vector_score=vector_by_id[chunk.id],
            keyword_score=keyword_by_id.get(chunk.id),
            hybrid_score=1 / (settings.rrf_k + rank),
        )
    for rank, (chunk, document, _) in enumerate(keyword_rows, start=1):
        if chunk.id not in fused:
            fused[chunk.id] = SearchResult(
                chunk_id=chunk.id,
                document_id=document.id,
                document_name=document.original_filename,
                content=chunk.content,
                page_number=chunk.page_number,
                section=chunk.section,
                vector_score=vector_by_id.get(chunk.id),
                keyword_score=keyword_by_id[chunk.id],
                hybrid_score=0.0,
            )
        fused[chunk.id].hybrid_score += 1 / (settings.rrf_k + rank)

    results = sorted(fused.values(), key=lambda item: item.hybrid_score, reverse=True)[:top_k]
    return results, provider.name
