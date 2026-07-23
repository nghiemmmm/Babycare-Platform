"""
Email Service Module - Quản lý việc gửi Email qua SMTP (Gmail, Custom SMTP).
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service chịu trách nhiệm kết nối SMTP và gửi Email thông báo / thư mời.
    """

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER") or os.getenv("MAIL_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("MAIL_PASSWORD")
        self.from_email = os.getenv("EMAILS_FROM_EMAIL") or self.smtp_user
        self.from_name = os.getenv("EMAILS_FROM_NAME", "BABY-CARE AI")

    def _send_email_smtp(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Gửi email qua giao thức SMTP (STARTTLS / SSL).
        """
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP configuration is missing. Cannot send email.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Đính kèm nội dung HTML
            html_part = MIMEText(html_content, "html", "utf-8")
            msg.attach(html_part)

            # Kết nối tới SMTP Server
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                server.ehlo()
                if self.smtp_port == 587:
                    server.starttls()
                    server.ehlo()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, [to_email], msg.as_string())

            logger.info(f"Successfully sent email to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_guardian_invitation_email(
        self,
        to_email: str,
        guardian_name: str,
        baby_name: str,
        role: str,
        inviter_name: str = "Bố/Mẹ",
        invitation_id: str = ""
    ) -> bool:
        """
        Gửi thư mời gia đình tham gia vòng tròn chăm sóc em bé.
        """
        role_label = {
          "ADMIN": "Quản trị viên (Toàn quyền)",
          "GUARDIAN": "Người chăm sóc (Quyền ghi chép)",
          "VIEWER": "Người xem (Chỉ xem thông tin)"
        }.get(role.upper(), "Người chăm sóc")

        subject = f"🍼 Thư mời tham gia chăm sóc {baby_name} trên BABY-CARE"
        accept_link = f"http://localhost:5173/?accept_invite={invitation_id}" if invitation_id else "http://localhost:5173"

        html_content = f"""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f8fa; margin: 0; padding: 20px; color: #334155; }}
                .card {{ max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 24px; padding: 32px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }}
                .logo {{ text-align: center; margin-bottom: 24px; }}
                .logo h1 {{ color: #1c648e; font-size: 24px; font-weight: 800; margin: 0; }}
                .badge {{ display: inline-block; background-color: #e0f2fe; color: #1c648e; font-weight: 700; padding: 6px 14px; border-radius: 20px; font-size: 12px; margin-bottom: 16px; }}
                h2 {{ color: #0f172a; font-size: 18px; font-weight: 700; margin-top: 0; }}
                p {{ font-size: 14px; line-height: 1.6; color: #475569; }}
                .info-box {{ background: #f8fafc; border-left: 4px solid #1c648e; border-radius: 8px; padding: 16px; margin: 20px 0; }}
                .info-box p {{ margin: 4px 0; font-size: 13px; }}
                .btn {{ display: inline-block; background-color: #1c648e; color: #ffffff !important; text-decoration: none; font-weight: 700; font-size: 14px; padding: 12px 28px; border-radius: 14px; margin-top: 16px; text-align: center; shadow: 0 4px 12px rgba(28,100,142,0.3); }}
                .footer {{ text-align: center; font-size: 11px; color: #94a3b8; margin-top: 32px; border-top: 1px solid #f1f5f9; padding-top: 16px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="logo">
                    <h1>👶 BABY-CARE AI</h1>
                </div>
                <div style="text-align: center;">
                    <span class="badge">VÒNG TRÒN GIA ĐÌNH</span>
                </div>
                <h2>Thư mời tham gia đồng hành cùng em bé</h2>
                <p>Xin chào <strong>{guardian_name}</strong>,</p>
                <p>Bạn vừa nhận được lời mời từ <strong>{inviter_name}</strong> tham gia vào nhóm chăm sóc bé <strong>{baby_name}</strong> trên ứng dụng BabyCare Platform.</p>
                
                <div class="info-box">
                    <p><strong>👶 Em bé:</strong> {baby_name}</p>
                    <p><strong>🛡️ Vai trò được phân quyền:</strong> {role_label}</p>
                    <p><strong>📧 Email nhận thư:</strong> {to_email}</p>
                </div>

                <p>Bằng việc tham gia, bạn có thể cùng theo dõi chỉ số tăng trưởng WHO, lịch bú sữa, giấc ngủ và nhận các nhắc nhở y tế quan trọng cho bé.</p>

                <div style="text-align: center;">
                    <a href="{accept_link}" class="btn">Chấp nhận Lời mời & Mở Ứng dụng</a>
                </div>

                <div class="footer">
                    <p>Email này được gửi tự động từ hệ thống BabyCare Platform.<br/>Nếu bạn không nhận ra yêu cầu này, vui lòng bỏ qua email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self._send_email_smtp(to_email, subject, html_content)

        return self._send_email_smtp(to_email, subject, html_content)
