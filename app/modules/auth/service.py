import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
import requests
from firebase_admin import auth
from google.cloud.firestore import Client
from app.core.config import settings
from app.infrastructure.database import get_firestore_db
from app.infrastructure.email.service import send_otp_email
from app.modules.auth.schemas import UserRecord
from app.shared.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidRegistrationDataError,
    InvalidPasswordResetCodeError,
    UpstreamTimeoutError,
)

logger = logging.getLogger(__name__)

FIREBASE_SIGN_IN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
FIREBASE_REFRESH_TOKEN_URL = "https://securetoken.googleapis.com/v1/token"
REQUEST_TIMEOUT_SECONDS = 8

# Cấu hình OTP đặt lại mật khẩu: 6 chữ số, hết hạn sau 10 phút, tối đa 5 lần thử sai
# trước khi mã bị vô hiệu hoá (buộc người dùng yêu cầu gửi lại mã mới).
OTP_COLLECTION = "password_reset_otps"
OTP_LENGTH = 6
OTP_TTL_MINUTES = 10
OTP_MAX_ATTEMPTS = 5


def _require_web_api_key() -> str:
    """Đảm bảo FIREBASE_WEB_API_KEY đã được cấu hình trước khi gọi Identity Toolkit REST API."""
    if not settings.FIREBASE_WEB_API_KEY:
        raise RuntimeError(
            "FIREBASE_WEB_API_KEY chưa được cấu hình trong .env "
            "(khác FIREBASE_CREDENTIALS_PATH — lấy tại Firebase Console > Project Settings > General > Web API Key)."
        )
    return settings.FIREBASE_WEB_API_KEY


def _sign_in_with_password(email: str, password: str) -> dict:
    """Xác thực email/mật khẩu qua Firebase Identity Toolkit REST API và trả về token."""
    api_key = _require_web_api_key()
    try:
        response = requests.post(
            FIREBASE_SIGN_IN_URL,
            params={"key": api_key},
            json={"email": email, "password": password, "returnSecureToken": True},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Lỗi kết nối Firebase Identity Toolkit (sign in): {e}")
        raise UpstreamTimeoutError("Không thể kết nối tới Firebase Authentication, vui lòng thử lại sau.")

    if response.status_code != 200:
        error_code = response.json().get("error", {}).get("message", "UNKNOWN_ERROR")
        logger.warning(f"Đăng nhập thất bại cho email {email}: {error_code}")
        raise InvalidCredentialsError()

    return response.json()


def _exchange_refresh_token(refresh_token: str) -> dict:
    """Đổi refresh token lấy ID token mới qua Firebase Secure Token REST API."""
    api_key = _require_web_api_key()
    try:
        response = requests.post(
            FIREBASE_REFRESH_TOKEN_URL,
            params={"key": api_key},
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Lỗi kết nối Firebase Secure Token API (refresh): {e}")
        raise UpstreamTimeoutError("Không thể kết nối tới Firebase Authentication, vui lòng thử lại sau.")

    if response.status_code != 200:
        error_code = response.json().get("error", {}).get("message", "UNKNOWN_ERROR")
        logger.warning(f"Refresh token thất bại: {error_code}")
        raise InvalidCredentialsError("Refresh token không hợp lệ hoặc đã hết hạn.")

    return response.json()


def register_user(email: str, password: str, name: Optional[str] = None, db: Client = None) -> dict:
    """
    Đăng ký tài khoản mới qua Firebase Admin SDK bằng email thật của người dùng, đăng nhập
    ngay để trả về token, và khởi tạo hồ sơ Firestore (JIT provisioning) để dùng được ngay
    không cần chờ /auth/me.
    """
    try:
        create_kwargs = {"email": email, "password": password}
        if name:
            create_kwargs["display_name"] = name
        user_record = auth.create_user(**create_kwargs)
    except auth.EmailAlreadyExistsError:
        raise EmailAlreadyExistsError()
    except ValueError as e:
        logger.warning(f"Dữ liệu đăng ký không hợp lệ cho email {email}: {e}")
        raise InvalidRegistrationDataError()

    logger.info(f"Đã tạo user Firebase mới: {user_record.uid}")

    token_data = _sign_in_with_password(email, password)

    user = UserRecord(uid=user_record.uid, email=email, name=name, picture=None)
    get_or_create_user_profile(user, db=db)

    return {
        "uid": user_record.uid,
        "email": email,
        "id_token": token_data["idToken"],
        "refresh_token": token_data["refreshToken"],
        "expires_in": int(token_data["expiresIn"]),
    }


def login_user(email: str, password: str, db: Client = None) -> dict:
    """
    Đăng nhập bằng email/mật khẩu qua Firebase Identity Toolkit, cập nhật last_login_at
    trong hồ sơ Firestore (tái dùng JIT provisioning) và trả về token.
    """
    token_data = _sign_in_with_password(email, password)

    user = UserRecord(uid=token_data["localId"], email=email, name=None, picture=None)
    get_or_create_user_profile(user, db=db)

    return {
        "uid": token_data["localId"],
        "email": email,
        "id_token": token_data["idToken"],
        "refresh_token": token_data["refreshToken"],
        "expires_in": int(token_data["expiresIn"]),
    }


def refresh_id_token(refresh_token: str) -> dict:
    """Làm mới ID token đã hết hạn bằng refresh token, không cần đăng nhập lại."""
    token_data = _exchange_refresh_token(refresh_token)

    return {
        "uid": token_data["user_id"],
        "email": None,
        "id_token": token_data["id_token"],
        "refresh_token": token_data["refresh_token"],
        "expires_in": int(token_data["expires_in"]),
    }

def _generate_otp() -> str:
    """Sinh ngẫu nhiên một mã OTP gồm OTP_LENGTH chữ số bằng CSPRNG."""
    return "".join(secrets.choice("0123456789") for _ in range(OTP_LENGTH))


def _hash_otp(otp: str, uid: str) -> str:
    """Băm mã OTP kèm uid làm salt, tránh lưu mã ở dạng plaintext trong Firestore."""
    return hashlib.sha256(f"{uid}:{otp}".encode()).hexdigest()


def request_password_reset(email: str, db: Client = None) -> None:
    """
    Sinh mã OTP 6 chữ số và gửi qua email tới chính email đăng nhập, nếu tài khoản đó tồn
    tại. Không raise lỗi và không tiết lộ qua kết quả trả về liệu email có tồn tại trong hệ
    thống hay không (tránh user enumeration) - caller (router) luôn trả về một thông báo
    chung chung cho client.
    """
    if db is None:
        db = get_firestore_db()

    try:
        user_record = auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        logger.info(f"Yêu cầu quên mật khẩu cho email không tồn tại: {email}")
        return

    otp = _generate_otp()
    now = datetime.now(timezone.utc)
    db.collection(OTP_COLLECTION).document(user_record.uid).set({
        "otp_hash": _hash_otp(otp, user_record.uid),
        "expires_at": (now + timedelta(minutes=OTP_TTL_MINUTES)).isoformat(),
        "attempts": 0,
        "created_at": now.isoformat(),
    })

    display_name = user_record.display_name or email
    send_otp_email(email, display_name, otp, OTP_TTL_MINUTES)


def _verify_otp(email: str, otp: str, db: Client) -> auth.UserRecord:
    """
    Kiểm tra mã OTP hợp lệ (đúng, chưa hết hạn, chưa vượt số lần thử) mà KHÔNG tiêu thụ mã -
    dùng chung cho bước xác thực OTP độc lập (`verify_password_reset_otp`) và bước đặt lại
    mật khẩu cuối cùng (`confirm_password_reset`). Trả về UserRecord của Firebase nếu hợp lệ,
    raise InvalidPasswordResetCodeError nếu không (không phân biệt lý do cụ thể cho client).
    """
    try:
        user_record = auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        raise InvalidPasswordResetCodeError()

    otp_ref = db.collection(OTP_COLLECTION).document(user_record.uid)
    otp_doc = otp_ref.get()
    if not otp_doc.exists:
        raise InvalidPasswordResetCodeError()

    data = otp_doc.to_dict()
    expires_at = datetime.fromisoformat(data["expires_at"])
    attempts = data.get("attempts", 0)

    if datetime.now(timezone.utc) >= expires_at or attempts >= OTP_MAX_ATTEMPTS:
        otp_ref.delete()
        raise InvalidPasswordResetCodeError()

    if not hmac.compare_digest(_hash_otp(otp, user_record.uid), data["otp_hash"]):
        otp_ref.update({"attempts": attempts + 1})
        logger.warning(f"Mã OTP sai cho {email} (lần thử {attempts + 1}/{OTP_MAX_ATTEMPTS}).")
        raise InvalidPasswordResetCodeError()

    return user_record


def verify_password_reset_otp(email: str, otp: str, db: Client = None) -> None:
    """
    Xác thực mã OTP đúng hay không mà chưa đặt mật khẩu mới - dùng để mở khoá bước nhập
    mật khẩu mới trên UI (chỉ hiện ô nhập mật khẩu sau khi mã đã được xác nhận đúng). Mã vẫn
    còn hiệu lực sau bước này, `confirm_password_reset` sẽ xác thực lại lần cuối trước khi ghi.
    """
    if db is None:
        db = get_firestore_db()
    _verify_otp(email, otp, db)


def confirm_password_reset(email: str, otp: str, new_password: str, db: Client = None) -> None:
    """
    Xác thực lại mã OTP rồi đặt mật khẩu mới trực tiếp bằng Firebase Admin SDK. Vì OTP đã tự
    xác nhận quyền sở hữu email, không cần thêm bước gọi Identity Toolkit REST API
    resetPassword (khác oobCode - không yêu cầu FIREBASE_WEB_API_KEY cho luồng này).
    """
    if db is None:
        db = get_firestore_db()

    user_record = _verify_otp(email, otp, db)

    auth.update_user(user_record.uid, password=new_password)
    db.collection(OTP_COLLECTION).document(user_record.uid).delete()
    logger.info(f"Đặt lại mật khẩu thành công qua OTP cho uid {user_record.uid}.")


def get_or_create_user_profile(user: UserRecord, db: Client = None) -> dict:
    """
    Check if user exists in the Firestore 'users' collection.
    If not, create a new profile document.
    Returns the user document data.
    """
    if db is None:
        db = get_firestore_db()

    user_ref = db.collection("users").document(user.uid)
    try:
        doc = user_ref.get()
        if doc.exists:
            # User exists, let's update last login time or just return the data
            user_data = doc.to_dict()
            user_ref.update({
                "last_login_at": datetime.now(timezone.utc).isoformat()
            })
            user_data["last_login_at"] = datetime.now(timezone.utc).isoformat()
            return user_data
        else:
            # User does not exist, let's create a new record (Just-in-Time provisioning)
            logger.info(f"Creating new user profile document for UID: {user.uid}")
            user_profile = {
                "email": user.email,
                "name": user.name,
                "role": "USER",
                "active": True,
                "first_login": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "last_login_at": datetime.now(timezone.utc).isoformat()
            }
            user_ref.set(user_profile)
            return user_profile
    except Exception as e:
        logger.error(f"Error getting or creating user profile in Firestore: {e}")
        raise e

def update_user_profile(uid: str, update_data: dict, db: Client = None) -> dict:
    """
    Cập nhật các trường thông tin trong hồ sơ người dùng trên Firestore.
    """
    if db is None:
        db = get_firestore_db()

    user_ref = db.collection("users").document(uid)
    try:
        # Lọc bỏ các giá trị None và cập nhật thời gian chỉnh sửa
        filtered_data = {k: v for k, v in update_data.items() if v is not None}
        filtered_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        user_ref.update(filtered_data)

        # Trả về dữ liệu mới nhất
        doc = user_ref.get()
        return doc.to_dict()
    except Exception as e:
        logger.error(f"Error updating user profile in Firestore: {e}")
        raise e
