from sqlalchemy import text

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import (
    Conversation,
    Document,
    DocumentChunk,
    IngestionJob,
    KnowledgeBase,
    Message,
    MessageCitation,
    User,
)


async def _migrate_embedding_dimension(connection) -> None:
    result = await connection.execute(text("""
        SELECT atttypmod
        FROM pg_attribute
        WHERE attrelid = 'document_chunks'::regclass
          AND attname = 'embedding'
          AND NOT attisdropped
    """))
    raw_typmod = result.scalar_one_or_none()
    current_dimension = raw_typmod
    if current_dimension is None or current_dimension == settings.embedding_dimensions:
        return
    if not isinstance(current_dimension, int) or current_dimension <= 0:
        raise RuntimeError("无法识别 document_chunks.embedding 的向量维度")

    # Changing vector dimensions requires clearing old vectors; chunks will be re-embedded on reprocessing.
    await connection.execute(text("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw"))
    target = int(settings.embedding_dimensions)
    await connection.execute(text(
        f"ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector({target}) "
        f"USING NULL::vector({target})"
    ))
    await connection.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw "
        "ON document_chunks USING hnsw (embedding vector_cosine_ops)"
    ))


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.run_sync(Base.metadata.create_all)
        await _migrate_embedding_dimension(connection)
