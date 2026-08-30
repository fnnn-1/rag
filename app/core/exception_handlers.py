import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.exception")


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "-")
    logger.exception("unhandled application error")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_server_error",
                "message": "服务器内部错误，请稍后重试。",
                "request_id": request_id,
            }
        },
        headers={"X-Request-ID": request_id},
    )
