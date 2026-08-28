from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "knowledge_base",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
)


@celery_app.task(name="app.tasks.ping")
def ping() -> dict[str, str]:
    return {"status": "ok", "message": "pong"}
