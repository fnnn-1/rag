from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine
from app.models import KnowledgeBase, User  # noqa: F401


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.run_sync(Base.metadata.create_all)
