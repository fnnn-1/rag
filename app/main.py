from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.knowledge_bases import router as knowledge_base_router
from app.api.search import router as search_router
from app.core.config import settings
from app.core.exception_handlers import unhandled_exception_handler
from app.core.logging import setup_logging
from app.core.middleware import RequestContextMiddleware
from app.db.init_db import init_db

setup_logging()
logger = logging.getLogger("app.lifecycle")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    logger.info("application started")
    yield
    logger.info("application stopped")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="企业级智能知识库问答系统 API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.add_middleware(RequestContextMiddleware)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(knowledge_base_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def root_health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "version": settings.app_version}
