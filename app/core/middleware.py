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

import uuid
from app.shared.context import request_trace_id, request_accumulated_cost

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware đo lường thời gian phản hồi và thiết lập Distributed Trace ID (X-Trace-ID).
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # Trích xuất X-Request-ID từ client header hoặc sinh trace_id mới
        incoming_trace_id = request.headers.get("X-Request-ID") or request.headers.get("X-Trace-ID")
        trace_id = incoming_trace_id if incoming_trace_id else f"trace_{uuid.uuid4().hex[:12]}"
        
        # Thiết lập vào ContextVar cho luồng request hiện tại
        request_trace_id.set(trace_id)
        request_accumulated_cost.set(0.0)

        start_time = time.time()
        try:
            response = await call_next(request)
        except Exception as e:
            logger.exception(f"[{trace_id}] Unhandled exception during request {request.method} {request.url.path}: {e}")
            raise e

        process_time = time.time() - start_time
        response.headers["X-Trace-ID"] = trace_id

        logger.info(
            f"[{trace_id}] Method: {request.method} | Path: {request.url.path} | "
            f"Status: {response.status_code} | Duration: {process_time:.4f}s"
        )
        return response

