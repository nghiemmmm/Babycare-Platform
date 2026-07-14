from unittest.mock import patch, MagicMock
import pytest
from fastapi import HTTPException, status
from firebase_admin import auth
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_get_current_user_valid_token():
    mock_creds = MagicMock()
    mock_creds.credentials = "valid_token"

    decoded_payload = {
        "uid": "user123",
        "email": "user@example.com",
        "name": "Jane Doe",
        "picture": "http://example.com/pic.jpg"
    }

    with patch("firebase_admin.auth.verify_id_token", return_value=decoded_payload) as mock_verify:
        result = await get_current_user(credentials=mock_creds)
        
        mock_verify.assert_called_once_with("valid_token")
        assert isinstance(result, UserRecord)
        assert result.uid == "user123"
        assert result.email == "user@example.com"
        assert result.name == "Jane Doe"
        assert result.picture == "http://example.com/pic.jpg"

@pytest.mark.anyio
async def test_get_current_user_expired_token():
    mock_creds = MagicMock()
    mock_creds.credentials = "expired_token"

    with patch("firebase_admin.auth.verify_id_token", side_effect=auth.ExpiredIdTokenError("Expired", "message")), \
         pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=mock_creds)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expired" in exc_info.value.detail.lower()

@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    mock_creds = MagicMock()
    mock_creds.credentials = "invalid_token"

    with patch("firebase_admin.auth.verify_id_token", side_effect=auth.InvalidIdTokenError("Invalid")), \
         pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=mock_creds)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid" in exc_info.value.detail.lower()

@pytest.mark.anyio
async def test_get_current_user_missing_credentials():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=None)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "required" in exc_info.value.detail.lower()
