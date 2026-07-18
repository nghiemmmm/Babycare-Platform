"""
Core Exception Handler Module

Registers custom domain exceptions to FastAPI application handlers.
"""
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.shared.exceptions import (
    AppException,
    EntityNotFoundError,
    PermissionDeniedError,
    UpstreamTimeoutError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidRegistrationDataError,
    InvalidPasswordResetCodeError,
    RateLimitExceededError,
)

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

    @app.exception_handler(UpstreamTimeoutError)
    async def upstream_timeout_handler(request: Request, exc: UpstreamTimeoutError) -> JSONResponse:
        logger.warning(f"Upstream timeout: {exc.message} on path {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={"message": exc.message}
        )

    @app.exception_handler(EmailAlreadyExistsError)
    async def email_already_exists_handler(request: Request, exc: EmailAlreadyExistsError) -> JSONResponse:
        logger.warning(f"Email already exists: {exc.message} on path {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"message": exc.message}
        )

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError) -> JSONResponse:
        logger.warning(f"Invalid credentials on path {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": exc.message}
        )

    @app.exception_handler(InvalidRegistrationDataError)
    async def invalid_registration_data_handler(request: Request, exc: InvalidRegistrationDataError) -> JSONResponse:
        logger.warning(f"Invalid registration data: {exc.message} on path {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": exc.message}
        )

    @app.exception_handler(InvalidPasswordResetCodeError)
    async def invalid_password_reset_code_handler(request: Request, exc: InvalidPasswordResetCodeError) -> JSONResponse:
        logger.warning(f"Invalid password reset code on path {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": exc.message}
        )

    @app.exception_handler(RateLimitExceededError)
    async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceededError) -> JSONResponse:
        logger.warning(f"Rate limit exceeded: {exc.message} on path {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
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
