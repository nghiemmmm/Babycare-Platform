import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from app.modules.auth.schemas import UserRecord

logger = logging.getLogger(__name__)

# Security scheme to extract Bearer token from Authorization header
security_scheme = HTTPBearer(auto_error=False)

from app.core.config import settings

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> UserRecord:
    """
    FastAPI dependency to extract and verify the Firebase ID Token.
    Returns the verified UserRecord if successful, otherwise raises 401.
    Supports a mock token bypass in local development environment.
    """
    if not credentials or credentials.credentials == "mock-token":
        if settings.APP_ENV == "local":
            return UserRecord(
                uid="mock-user-id",
                email="mock@family.com",
                name="Elena Parent",
                picture=None
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization credentials are required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    try:
        # Verify token using Firebase Admin SDK
        decoded_token = auth.verify_id_token(token)
        return UserRecord(
            uid=decoded_token.get("uid"),
            email=decoded_token.get("email"),
            name=decoded_token.get("name"),
            picture=decoded_token.get("picture")
        )
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        if settings.APP_ENV.lower() in ["local", "development", "dev"]:
            logger.info("[Dev Bypass] Token verification error bypassed in local mode.")
            return UserRecord(
                uid="mock-user-id",
                email="nghiem@babycare.com",
                name="Minh Anh (Mẹ bé Leo)",
                picture=None
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
