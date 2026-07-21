"""
Email Sending Module

Cung cấp gửi email dạng fail-open: nếu SMTP chưa được cấu hình hoặc gửi
thất bại, chỉ log warning thay vì raise lỗi lên caller. Áp dụng cùng
nguyên tắc với app/infrastructure/cache/redis.py — tính năng phụ thuộc
(vd. quên mật khẩu) vẫn chạy được, chỉ không gửi được email thật.
"""
import html
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Gửi một email HTML qua SMTP. Trả về True nếu gửi thành công, False nếu bỏ qua/thất bại."""
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP chưa được cấu hình - bỏ qua gửi email tới %s.", to_email)
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
    message["To"] = to_email
    message.set_content("Vui lòng dùng trình đọc email hỗ trợ HTML để xem nội dung này.")
    message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
        return True
    except Exception as e:
        logger.error("Gửi email tới %s thất bại: %s", to_email, e)
        return False


def send_otp_email(to_email: str, display_name: str, otp: str, ttl_minutes: int) -> bool:
    """Gửi email chứa mã OTP đặt lại mật khẩu cho một tài khoản BabyCare."""
    subject = "BabyCare AI - Mã xác thực đặt lại mật khẩu"
    safe_display_name = html.escape(display_name)
    html_body = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
      <h2>Đặt lại mật khẩu BabyCare AI</h2>
      <p>Xin chào <strong>{safe_display_name}</strong>,</p>
      <p>Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản của bạn. Nhập mã xác thực sau đây trong ứng dụng để tiếp tục:</p>
      <p style="margin: 24px 0; text-align: center;">
        <span style="display:inline-block;background:#f2f5f0;color:#1f2d22;font-size:32px;font-weight:700;letter-spacing:8px;padding:16px 24px;border-radius:8px;">{otp}</span>
      </p>
      <p>Mã có hiệu lực trong {ttl_minutes} phút. Nếu bạn không yêu cầu điều này, có thể bỏ qua email này - mật khẩu của bạn sẽ không bị thay đổi.</p>
      <p style="color:#888;font-size:12px;">Không chia sẻ mã này với bất kỳ ai, kể cả nhân viên BabyCare AI.</p>
    </div>
    """
    return send_email(to_email, subject, html_body)
