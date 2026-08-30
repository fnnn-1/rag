from dataclasses import dataclass
from time import perf_counter
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.llm.chat import FallbackLLMProvider, get_llm_provider
from app.models import Conversation, Message, MessageCitation, User
from app.retrieval.hybrid_search import SearchResult, hybrid_search
from app.retrieval.reranker import RerankedResult, has_sufficient_evidence, rerank_results, select_evidence

REFUSAL_ANSWER = "知识库中未找到足够依据，无法准确回答该问题。"


@dataclass(slots=True)
class RAGAnswer:
    answer: str
    grounded: bool
    conversation_id: UUID
    message_id: UUID
    trace_id: str
    citations: list[MessageCitation]
    citation_results: list[RerankedResult]
    retrieval_latency_ms: int
    generation_latency_ms: int
    llm_provider: str


async def _get_or_create_conversation(
    db: AsyncSession,
    user: User,
    knowledge_base_id: UUID,
    conversation_id: UUID | None,
    question: str,
) -> Conversation:
    if conversation_id is not None:
        conversation = await db.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id,
                Conversation.knowledge_base_id == knowledge_base_id,
            )
        )
        if conversation is None:
            raise ValueError("会话不存在或无权访问")
        return conversation

    conversation = Conversation(
        user_id=user.id,
        knowledge_base_id=knowledge_base_id,
        title=question.strip()[:200],
    )
    db.add(conversation)
    await db.flush()
    return conversation


async def answer_question(
    db: AsyncSession,
    user: User,
    knowledge_base_id: UUID,
    question: str,
    conversation_id: UUID | None,
    top_k: int,
) -> RAGAnswer:
    trace_id = uuid4().hex
    retrieval_start = perf_counter()
    candidates, _ = await hybrid_search(
        db,
        knowledge_base_id,
        question,
        top_k=max(top_k, min(settings.retrieval_candidate_k, 20)),
    )
    reranked = rerank_results(question, candidates, top_k=max(top_k, 5))
    evidence = select_evidence(reranked)
    grounded = has_sufficient_evidence(evidence)
    retrieval_latency_ms = round((perf_counter() - retrieval_start) * 1000)

    if grounded:
        selected = evidence[:top_k]
        selected_results = [item.result for item in selected]
        generation_start = perf_counter()
        provider = get_llm_provider()
        try:
            try:
                answer = await provider.generate(question, selected_results)
                provider_name = provider.name
            finally:
                await provider.close()
        except Exception:
            fallback = FallbackLLMProvider()
            answer = await fallback.generate(question, selected_results)
            provider_name = "extractive-fallback-after-error"
        generation_latency_ms = round((perf_counter() - generation_start) * 1000)
    else:
        selected = []
        selected_results = []
        answer = REFUSAL_ANSWER
        generation_latency_ms = 0
        provider_name = "evidence-gate"

    conversation = await _get_or_create_conversation(
        db, user, knowledge_base_id, conversation_id, question
    )
    db.add(Message(
        conversation_id=conversation.id,
        role="user",
        content=question.strip(),
        grounded=False,
        trace_id=trace_id,
    ))
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        grounded=grounded,
        trace_id=trace_id,
        retrieval_latency_ms=retrieval_latency_ms,
        generation_latency_ms=generation_latency_ms,
    )
    db.add(assistant_message)
    await db.flush()

    citations = []
    for index, item in enumerate(selected, start=1):
        citation = MessageCitation(
            message_id=assistant_message.id,
            chunk_id=item.result.chunk_id,
            citation_index=index,
            rerank_score=item.rerank_score,
        )
        db.add(citation)
        citations.append(citation)
    await db.commit()
    await db.refresh(assistant_message)
    return RAGAnswer(
        answer=answer,
        grounded=grounded,
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        trace_id=trace_id,
        citations=citations,
        citation_results=selected,
        retrieval_latency_ms=retrieval_latency_ms,
        generation_latency_ms=generation_latency_ms,
        llm_provider=provider_name,
    )
