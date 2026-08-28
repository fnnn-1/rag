from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import KnowledgeBase, User
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseResponse, KnowledgeBaseUpdate

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


async def get_owned_knowledge_base(
    knowledge_base_id: UUID,
    user: User,
    db: AsyncSession,
) -> KnowledgeBase:
    knowledge_base = await db.scalar(
        select(KnowledgeBase).where(
            KnowledgeBase.id == knowledge_base_id,
            KnowledgeBase.owner_id == user.id,
        )
    )
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在或无权访问")
    return knowledge_base


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBase:
    knowledge_base = KnowledgeBase(
        owner_id=user.id,
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
    )
    db.add(knowledge_base)
    await db.commit()
    await db.refresh(knowledge_base)
    return knowledge_base


@router.get("", response_model=list[KnowledgeBaseResponse])
async def list_knowledge_bases(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[KnowledgeBase]:
    result = await db.scalars(
        select(KnowledgeBase)
        .where(KnowledgeBase.owner_id == user.id)
        .order_by(KnowledgeBase.created_at.desc())
    )
    return list(result.all())


@router.get("/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    knowledge_base_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBase:
    return await get_owned_knowledge_base(knowledge_base_id, user, db)


@router.patch("/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    knowledge_base_id: UUID,
    payload: KnowledgeBaseUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBase:
    knowledge_base = await get_owned_knowledge_base(knowledge_base_id, user, db)
    if payload.name is not None:
        knowledge_base.name = payload.name.strip()
    if payload.description is not None:
        knowledge_base.description = payload.description.strip() or None
    await db.commit()
    await db.refresh(knowledge_base)
    return knowledge_base


@router.delete("/{knowledge_base_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    knowledge_base_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    knowledge_base = await get_owned_knowledge_base(knowledge_base_id, user, db)
    await db.delete(knowledge_base)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
