from time import monotonic

from fastapi import APIRouter, Response, status
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal

router = APIRouter(tags=["system"])
STARTED_AT = monotonic()


async def dependency_status() -> dict[str, str]:
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
    return {"database": database_status, "redis": redis_status}


@router.get("/health/live", summary="进程存活检查")
async def liveness() -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "uptime_seconds": round(monotonic() - STARTED_AT, 2),
    }


@router.get("/health/ready", summary="数据库和 Redis 就绪检查")
async def readiness(response: Response) -> dict:
    dependencies = await dependency_status()
    ready = all(value == "ok" for value in dependencies.values())
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ok" if ready else "degraded",
        "service": settings.app_name,
        "version": settings.app_version,
        "dependencies": dependencies,
    }


@router.get("/health", summary="兼容健康检查")
async def health_check(response: Response) -> dict:
    return await readiness(response)
