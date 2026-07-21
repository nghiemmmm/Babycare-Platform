from fastapi import APIRouter, Depends
from app.shared.concurrency import run_in_threadpool
from app.shared.schemas import Message
from app.shared.rate_limit import rate_limiter
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import (
    UserRecord,
    UserMeResponse,
    UserProfileUpdate,
    UserProfileResponse,
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    VerifyOtpRequest,
    ResetPasswordRequest,
    AuthTokenResponse,
)
from app.modules.auth.service import (
    get_or_create_user_profile,
    update_user_profile,
    register_user,
    login_user,
    refresh_id_token,
    request_password_reset,
    verify_password_reset_otp,
    confirm_password_reset,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Giới hạn số lần gọi theo IP để chống brute-force mật khẩu / spam đăng ký / spam email
# quên mật khẩu (xem app/shared/rate_limit.py).
_register_rate_limit = rate_limiter("register", max_attempts=5, window_seconds=600)
_login_rate_limit = rate_limiter("login", max_attempts=10, window_seconds=300)
_refresh_rate_limit = rate_limiter("refresh", max_attempts=20, window_seconds=300)
_forgot_password_rate_limit = rate_limiter("forgot-password", max_attempts=5, window_seconds=600)
# Giới hạn riêng cho việc thử mã OTP (ngoài giới hạn 5 lần thử sai/mã ở service layer) -
# chặn một IP dò nhiều mã OTP của nhiều tài khoản khác nhau trong cùng khung giờ.
_verify_otp_rate_limit = rate_limiter("verify-reset-otp", max_attempts=10, window_seconds=600)
_reset_password_rate_limit = rate_limiter("reset-password", max_attempts=10, window_seconds=600)

@router.post("/register", response_model=AuthTokenResponse, status_code=201, dependencies=[Depends(_register_rate_limit)])
async def register(payload: RegisterRequest):
    """
    Đăng ký tài khoản mới qua Firebase Authentication và trả về token đăng nhập ngay.
    """
    return await run_in_threadpool(register_user, payload.email, payload.password, payload.name)

@router.post("/login", response_model=AuthTokenResponse, dependencies=[Depends(_login_rate_limit)])
async def login(payload: LoginRequest):
    """
    Đăng nhập bằng email/mật khẩu qua Firebase Authentication.
    """
    return await run_in_threadpool(login_user, payload.email, payload.password)

@router.post("/refresh", response_model=AuthTokenResponse, dependencies=[Depends(_refresh_rate_limit)])
async def refresh(payload: RefreshTokenRequest):
    """
    Làm mới ID token đã hết hạn bằng refresh token, không cần đăng nhập lại.
    """
    return await run_in_threadpool(refresh_id_token, payload.refresh_token)

@router.post("/forgot-password", response_model=Message, dependencies=[Depends(_forgot_password_rate_limit)])
async def forgot_password(payload: ForgotPasswordRequest):
    """
    Gửi mã OTP đặt lại mật khẩu qua email nếu tài khoản ứng với email này tồn tại. Luôn trả
    về cùng một thông báo bất kể email có tồn tại hay không, để tránh lộ thông tin tài khoản
    nào đang tồn tại trong hệ thống (user enumeration).
    """
    await run_in_threadpool(request_password_reset, payload.email)
    return Message(
        message="Nếu tài khoản tồn tại, một mã xác thực đã được gửi tới email của bạn."
    )

@router.post("/verify-reset-otp", response_model=Message, dependencies=[Depends(_verify_otp_rate_limit)])
async def verify_reset_otp(payload: VerifyOtpRequest):
    """
    Kiểm tra mã OTP đúng hay không, dùng để mở khoá bước nhập mật khẩu mới trên UI. Mã vẫn
    còn hiệu lực sau khi gọi endpoint này - `/auth/reset-password` sẽ xác thực lại lần cuối.
    """
    await run_in_threadpool(verify_password_reset_otp, payload.email, payload.otp)
    return Message(message="Mã xác thực hợp lệ.")

@router.post("/reset-password", response_model=Message, dependencies=[Depends(_reset_password_rate_limit)])
async def reset_password(payload: ResetPasswordRequest):
    """
    Đặt mật khẩu mới bằng mã OTP 6 chữ số nhận được từ email đặt lại mật khẩu.
    """
    await run_in_threadpool(confirm_password_reset, payload.email, payload.otp, payload.new_password)
    return Message(message="Đặt lại mật khẩu thành công. Bạn có thể đăng nhập với mật khẩu mới.")

@router.get("/me", response_model=UserMeResponse)
async def get_my_profile(current_user: UserRecord = Depends(get_current_user)):
    """
    Lấy thông tin hồ sơ của người dùng hiện tại đang đăng nhập.
    Tự động khởi tạo thông tin trống trong Firestore ở lần đăng nhập đầu tiên.
    """
    profile = await run_in_threadpool(get_or_create_user_profile, current_user)
    return {
        "uid": current_user.uid,
        "email": current_user.email,
        "name": current_user.name,
        "picture": current_user.picture,
        "profile": profile
    }

@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    update_data: UserProfileUpdate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Cập nhật thông tin hồ sơ người dùng trong Firestore (tên hiển thị, số điện thoại).
    """
    # Convert Pydantic object sang dict và loại bỏ các giá trị không được truyền lên (unset)
    data = update_data.model_dump(exclude_unset=True)
    updated_profile = await run_in_threadpool(update_user_profile, current_user.uid, data)
    return updated_profile
