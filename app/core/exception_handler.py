"""
Core Exception Handler Module

Registers custom domain exceptions to FastAPI application handlers.
"""
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.shared.exceptions import AppException, EntityNotFoundError, PermissionDeniedError

logger = logging.getLogger(__name__)

def init_app(app: FastAPI) -> None:
    """
    Đăng ký các global exception handler để xử lý các ngoại lệ nghiệp vụ.
    """
    
    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
        logger.warning(f"Entity not found: {exc.message} on path {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": exc.message}
        )

    @app.exception_handler(PermissionDeniedError)
    async def permission_denied_handler(request: Request, exc: PermissionDeniedError) -> JSONResponse:
        logger.warning(f"Permission denied: {exc.message} on path {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"message": exc.message}
        )

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.error(f"Application error: {exc} on path {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau."}
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled system error on path {request.url.path}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Đã xảy ra lỗi hệ thống không xác định."}
        )
