"""
Test Authentication Service & Firebase Auth Token Validation
"""
from unittest.mock import patch, MagicMock
import pytest
from app.modules.auth import service as auth_service
from app.modules.auth.dependencies import get_current_user
from app.shared.exceptions import InvalidCredentialsError


def test_register_user_success():
    """Kiểm tra luồng đăng ký tài khoản thành công"""
    with patch("app.modules.auth.service.auth.create_user") as mock_fb_create, \
         patch("app.modules.auth.service._sign_in_with_password", return_value={"idToken": "mock_id_token", "refreshToken": "mock_rf", "expiresIn": "3600"}), \
         patch("app.modules.auth.service.get_or_create_user_profile"):
        
        mock_fb_user = MagicMock()
        mock_fb_user.uid = "uid_test_123"
        mock_fb_create.return_value = mock_fb_user

        token_data = auth_service.register_user(
            email="test@babycare.com",
            password="Password123!",
            name="Mẹ Bé"
        )
        assert token_data["id_token"] == "mock_id_token"


def test_login_user_invalid_credentials():
    """Kiểm tra xử lý đăng nhập thất bại khi sai mật khẩu"""
    with patch("app.modules.auth.service.requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {"error": {"message": "INVALID_PASSWORD"}}
        mock_post.return_value = mock_resp

        with pytest.raises(InvalidCredentialsError):
            auth_service.login_user("test@babycare.com", "WrongPassword")


@pytest.mark.anyio
async def test_get_current_user_valid_token():
    """Kiểm tra xác thực Firebase JWT Bearer Token"""
    mock_creds = MagicMock()
    mock_creds.credentials = "valid_jwt_token"
    
    with patch("app.modules.auth.dependencies.auth.verify_id_token", return_value={"uid": "user_123", "email": "test@babycare.com", "name": "Mẹ Leo", "picture": None}):
        user = await get_current_user(mock_creds)
        assert user.uid == "user_123"
        assert user.email == "test@babycare.com"
