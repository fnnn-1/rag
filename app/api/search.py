from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.api.knowledge_bases import get_owned_knowledge_base
from app.db.session import get_db
from app.models import User
from app.retrieval.hybrid_search import hybrid_search
from app.schemas.search import SearchRequest, SearchResponse, SearchResultResponse

router = APIRouter(tags=["retrieval"])


@router.post("/knowledge-bases/{knowledge_base_id}/search", response_model=SearchResponse)
async def search_knowledge_base(
    knowledge_base_id: UUID,
    payload: SearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    await get_owned_knowledge_base(knowledge_base_id, user, db)
    results, provider_name = await hybrid_search(db, knowledge_base_id, payload.query, payload.top_k)
    return SearchResponse(
        query=payload.query,
        results=[SearchResultResponse.model_validate(result, from_attributes=True) for result in results],
        embedding_provider=provider_name,
        result_count=len(results),
    )
