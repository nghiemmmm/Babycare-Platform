"""
Core Middleware Module

Defines custom middlewares for FastAPI application.
"""
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware đo lường và ghi log chi tiết thời gian phản hồi của mỗi request.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        try:
            response = await call_next(request)
        except Exception as e:
            logger.exception(f"Unhandled exception during request {request.method} {request.url.path}: {e}")
            raise e
        process_time = time.time() - start_time
        logger.info(
            f"Method: {request.method} | Path: {request.url.path} | "
            f"Status: {response.status_code} | Duration: {process_time:.4f}s"
        )
        return response
