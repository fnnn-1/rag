from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.config import settings
from app.db.session import SessionLocal

router = APIRouter(tags=["system"])


@router.get("/health", summary="检查 API、数据库和 Redis 状态")
async def health_check() -> dict:
    database_status = "ok"
    redis_status = "ok"

    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        database_status = "error"

    redis = Redis.from_url(settings.redis_url)
    try:
        await redis.ping()
    except Exception:
        redis_status = "error"
    finally:
        await redis.aclose()

    overall = "ok" if database_status == redis_status == "ok" else "degraded"
    return {
        "status": overall,
        "service": settings.app_name,
        "version": settings.app_version,
        "dependencies": {
            "database": database_status,
            "redis": redis_status,
        },
    }
