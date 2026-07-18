from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
import pytest
from firebase_admin import auth as firebase_auth
from app.modules.auth.service import (
    register_user,
    login_user,
    refresh_id_token,
    request_password_reset,
    verify_password_reset_otp,
    confirm_password_reset,
    get_or_create_user_profile,
    update_user_profile,
    _hash_otp,
)
from app.modules.auth.schemas import UserRecord
from app.shared.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidPasswordResetCodeError,
)


@pytest.fixture(autouse=True)
def mock_web_api_key():
    with patch("app.modules.auth.service.settings.FIREBASE_WEB_API_KEY", "fake-web-api-key"):
        yield


@pytest.fixture
def mock_get_or_create_profile():
    with patch("app.modules.auth.service.get_or_create_user_profile") as mock:
        yield mock


def _mock_response(status_code: int, payload: dict):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload
    return response


def test_register_user_success(mock_get_or_create_profile):
    fake_user_record = MagicMock(uid="uid123")
    sign_in_payload = {
        "idToken": "id-token-abc",
        "refreshToken": "refresh-token-abc",
        "expiresIn": "3600",
    }

    with patch("app.modules.auth.service.auth.create_user", return_value=fake_user_record) as mock_create_user, \
         patch("app.modules.auth.service.requests.post", return_value=_mock_response(200, sign_in_payload)):
        result = register_user("newuser@example.com", "secret123", name="New User")

    mock_create_user.assert_called_once_with(email="newuser@example.com", password="secret123", display_name="New User")
    mock_get_or_create_profile.assert_called_once()
    assert result["uid"] == "uid123"
    assert result["email"] == "newuser@example.com"
    assert result["id_token"] == "id-token-abc"
    assert result["refresh_token"] == "refresh-token-abc"
    assert result["expires_in"] == 3600


def test_register_user_email_already_exists(mock_get_or_create_profile):
    with patch(
        "app.modules.auth.service.auth.create_user",
        side_effect=firebase_auth.EmailAlreadyExistsError(message="exists", cause=None, http_response=None),
    ):
        with pytest.raises(EmailAlreadyExistsError):
            register_user("dup@example.com", "secret123")

    mock_get_or_create_profile.assert_not_called()


def test_login_user_success(mock_get_or_create_profile):
    sign_in_payload = {
        "localId": "uid456",
        "idToken": "id-token-xyz",
        "refreshToken": "refresh-token-xyz",
        "expiresIn": "3600",
    }

    with patch("app.modules.auth.service.requests.post", return_value=_mock_response(200, sign_in_payload)) as mock_post:
        result = login_user("someuser@example.com", "secret123")

    assert mock_post.call_args.kwargs["json"]["email"] == "someuser@example.com"
    mock_get_or_create_profile.assert_called_once()
    assert result["uid"] == "uid456"
    assert result["id_token"] == "id-token-xyz"


def test_login_user_invalid_credentials(mock_get_or_create_profile):
    error_payload = {"error": {"message": "INVALID_LOGIN_CREDENTIALS"}}

    with patch("app.modules.auth.service.requests.post", return_value=_mock_response(400, error_payload)):
        with pytest.raises(InvalidCredentialsError):
            login_user("someuser@example.com", "wrong-password")

    mock_get_or_create_profile.assert_not_called()


def test_refresh_id_token_success():
    refresh_payload = {
        "user_id": "uid789",
        "id_token": "new-id-token",
        "refresh_token": "new-refresh-token",
        "expires_in": "3600",
    }

    with patch("app.modules.auth.service.requests.post", return_value=_mock_response(200, refresh_payload)):
        result = refresh_id_token("some-refresh-token")

    assert result["uid"] == "uid789"
    assert result["id_token"] == "new-id-token"
    assert result["expires_in"] == 3600


def _mock_otp_db(exists: bool, data: dict = None):
    doc_ref = MagicMock()
    doc_ref.get.return_value = MagicMock(exists=exists, **({"to_dict.return_value": data} if data else {}))
    db = MagicMock()
    db.collection.return_value.document.return_value = doc_ref
    return db, doc_ref


def test_request_password_reset_sends_otp_when_account_exists():
    fake_user_record = MagicMock(uid="uid123", display_name="Some User")
    db, otp_ref = _mock_otp_db(exists=False)

    with patch("app.modules.auth.service.auth.get_user_by_email", return_value=fake_user_record), \
         patch("app.modules.auth.service.send_otp_email") as mock_send_email:
        request_password_reset("someuser@example.com", db=db)

    otp_ref.set.assert_called_once()
    saved = otp_ref.set.call_args.args[0]
    assert set(saved.keys()) == {"otp_hash", "expires_at", "attempts", "created_at"}
    assert saved["attempts"] == 0
    mock_send_email.assert_called_once()
    assert mock_send_email.call_args.args[0] == "someuser@example.com"
    assert mock_send_email.call_args.args[1] == "Some User"
    assert len(mock_send_email.call_args.args[2]) == 6 and mock_send_email.call_args.args[2].isdigit()


def test_request_password_reset_falls_back_to_email_when_no_display_name():
    fake_user_record = MagicMock(uid="uid123", display_name=None)
    db, _ = _mock_otp_db(exists=False)

    with patch("app.modules.auth.service.auth.get_user_by_email", return_value=fake_user_record), \
         patch("app.modules.auth.service.send_otp_email") as mock_send_email:
        request_password_reset("someuser@example.com", db=db)

    assert mock_send_email.call_args.args[1] == "someuser@example.com"


def test_request_password_reset_user_not_found_is_silent():
    db, otp_ref = _mock_otp_db(exists=False)

    with patch(
        "app.modules.auth.service.auth.get_user_by_email",
        side_effect=firebase_auth.UserNotFoundError(message="not found"),
    ), patch("app.modules.auth.service.send_otp_email") as mock_send_email:
        request_password_reset("ghost@example.com", db=db)

    mock_send_email.assert_not_called()
    otp_ref.set.assert_not_called()


def test_verify_password_reset_otp_success_does_not_consume_code():
    fake_user_record = MagicMock(uid="uid123")
    otp_data = {
        "otp_hash": _hash_otp("123456", "uid123"),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        "attempts": 0,
    }
    db, otp_ref = _mock_otp_db(exists=True, data=otp_data)

    with patch("app.modules.auth.service.auth.get_user_by_email", return_value=fake_user_record):
        verify_password_reset_otp("someuser@example.com", "123456", db=db)

    otp_ref.delete.assert_not_called()
    otp_ref.update.assert_not_called()


def test_verify_password_reset_otp_wrong_code_increments_attempts():
    fake_user_record = MagicMock(uid="uid123")
    otp_data = {
        "otp_hash": _hash_otp("123456", "uid123"),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        "attempts": 0,
    }
    db, otp_ref = _mock_otp_db(exists=True, data=otp_data)

    with patch("app.modules.auth.service.auth.get_user_by_email", return_value=fake_user_record):
        with pytest.raises(InvalidPasswordResetCodeError):
            verify_password_reset_otp("someuser@example.com", "000000", db=db)

    otp_ref.update.assert_called_once_with({"attempts": 1})


def test_confirm_password_reset_success():
    fake_user_record = MagicMock(uid="uid123")
    otp_data = {
        "otp_hash": _hash_otp("123456", "uid123"),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        "attempts": 0,
    }
    db, otp_ref = _mock_otp_db(exists=True, data=otp_data)

    with patch("app.modules.auth.service.auth.get_user_by_email", return_value=fake_user_record), \
         patch("app.modules.auth.service.auth.update_user") as mock_update_user:
        confirm_password_reset("someuser@example.com", "123456", "newsecret123", db=db)

    mock_update_user.assert_called_once_with("uid123", password="newsecret123")
    otp_ref.delete.assert_called_once()


def test_confirm_password_reset_wrong_otp_increments_attempts():
    fake_user_record = MagicMock(uid="uid123")
    otp_data = {
        "otp_hash": _hash_otp("123456", "uid123"),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        "attempts": 1,
    }
    db, otp_ref = _mock_otp_db(exists=True, data=otp_data)

    with patch("app.modules.auth.service.auth.get_user_by_email", return_value=fake_user_record), \
         patch("app.modules.auth.service.auth.update_user") as mock_update_user:
        with pytest.raises(InvalidPasswordResetCodeError):
            confirm_password_reset("someuser@example.com", "000000", "newsecret123", db=db)

    mock_update_user.assert_not_called()
    otp_ref.update.assert_called_once_with({"attempts": 2})


def test_confirm_password_reset_expired_code():
    fake_user_record = MagicMock(uid="uid123")
    otp_data = {
        "otp_hash": _hash_otp("123456", "uid123"),
        "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
        "attempts": 0,
    }
    db, otp_ref = _mock_otp_db(exists=True, data=otp_data)

    with patch("app.modules.auth.service.auth.get_user_by_email", return_value=fake_user_record):
        with pytest.raises(InvalidPasswordResetCodeError):
            confirm_password_reset("someuser@example.com", "123456", "newsecret123", db=db)

    otp_ref.delete.assert_called_once()


def test_confirm_password_reset_too_many_attempts():
    fake_user_record = MagicMock(uid="uid123")
    otp_data = {
        "otp_hash": _hash_otp("123456", "uid123"),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        "attempts": 5,
    }
    db, otp_ref = _mock_otp_db(exists=True, data=otp_data)

    with patch("app.modules.auth.service.auth.get_user_by_email", return_value=fake_user_record):
        with pytest.raises(InvalidPasswordResetCodeError):
            confirm_password_reset("someuser@example.com", "123456", "newsecret123", db=db)

    otp_ref.delete.assert_called_once()


def test_confirm_password_reset_no_otp_requested():
    fake_user_record = MagicMock(uid="uid123")
    db, otp_ref = _mock_otp_db(exists=False)

    with patch("app.modules.auth.service.auth.get_user_by_email", return_value=fake_user_record):
        with pytest.raises(InvalidPasswordResetCodeError):
            confirm_password_reset("someuser@example.com", "123456", "newsecret123", db=db)


def test_confirm_password_reset_user_not_found():
    db, _ = _mock_otp_db(exists=False)

    with patch(
        "app.modules.auth.service.auth.get_user_by_email",
        side_effect=firebase_auth.UserNotFoundError(message="not found"),
    ):
        with pytest.raises(InvalidPasswordResetCodeError):
            confirm_password_reset("ghost@example.com", "123456", "newsecret123", db=db)


def _mock_db_with_user_ref():
    user_ref = MagicMock()
    db = MagicMock()
    db.collection.return_value.document.return_value = user_ref
    return db, user_ref


def test_get_or_create_user_profile_creates_new_on_first_login():
    db, user_ref = _mock_db_with_user_ref()
    user_ref.get.return_value = MagicMock(exists=False)

    user = UserRecord(uid="uid123", email="newuser@example.com", name="New User", picture=None)
    result = get_or_create_user_profile(user, db=db)

    user_ref.set.assert_called_once()
    created_profile = user_ref.set.call_args.args[0]
    assert created_profile["email"] == "newuser@example.com"
    assert created_profile["name"] == "New User"
    assert created_profile["role"] == "USER"
    assert "username" not in created_profile
    assert result == created_profile
    user_ref.update.assert_not_called()


def test_get_or_create_user_profile_updates_last_login_for_existing_user():
    db, user_ref = _mock_db_with_user_ref()
    existing_data = {"email": "someuser@example.com", "name": "Some User", "role": "USER"}
    user_ref.get.return_value = MagicMock(exists=True, **{"to_dict.return_value": existing_data})

    user = UserRecord(uid="uid123", email="someuser@example.com", name=None, picture=None)
    result = get_or_create_user_profile(user, db=db)

    user_ref.set.assert_not_called()
    user_ref.update.assert_called_once()
    assert "last_login_at" in user_ref.update.call_args.args[0]
    assert result["email"] == "someuser@example.com"
    assert "last_login_at" in result


def test_update_user_profile_filters_none_values():
    db, user_ref = _mock_db_with_user_ref()
    user_ref.get.return_value = MagicMock(**{"to_dict.return_value": {"phone": "0900000000"}})

    update_user_profile("uid123", {"phone": "0900000000", "name": None}, db=db)

    user_ref.update.assert_called_once()
    sent_data = user_ref.update.call_args.args[0]
    assert sent_data["phone"] == "0900000000"
    assert "name" not in sent_data
    assert "updated_at" in sent_data
