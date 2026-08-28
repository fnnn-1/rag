from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.api.knowledge_bases import get_owned_knowledge_base
from app.db.session import get_db
from app.models import User
from app.schemas.chat import ChatRequest, ChatResponse, CitationResponse
from app.services.rag_service import answer_question

router = APIRouter(tags=["chat"])


@router.post("/chat/query", response_model=ChatResponse)
async def query_knowledge_base(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    await get_owned_knowledge_base(payload.knowledge_base_id, user, db)
    try:
        answer = await answer_question(
            db=db,
            user=user,
            knowledge_base_id=payload.knowledge_base_id,
            question=payload.question,
            conversation_id=payload.conversation_id,
            top_k=payload.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    citations = []
    for index, item in enumerate(answer.citation_results, start=1):
        result = item.result
        citations.append(CitationResponse(
            citation_index=index,
            document_id=result.document_id,
            document_name=result.document_name,
            chunk_id=result.chunk_id,
            content=result.content,
            page_number=result.page_number,
            section=result.section,
            rerank_score=item.rerank_score,
        ))
    return ChatResponse(
        answer=answer.answer,
        grounded=answer.grounded,
        conversation_id=answer.conversation_id,
        message_id=answer.message_id,
        trace_id=answer.trace_id,
        citations=citations,
        retrieval_latency_ms=answer.retrieval_latency_ms,
        generation_latency_ms=answer.generation_latency_ms,
        llm_provider=answer.llm_provider,
    )
