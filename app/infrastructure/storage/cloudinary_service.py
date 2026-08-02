"""
Cloudinary Storage Module

Upload ảnh đại diện bé và file ghi âm tiếng khóc lên Cloudinary. Áp dụng cùng
nguyên tắc fail-open như app/infrastructure/email/service.py: nếu chưa cấu hình
CLOUDINARY_CLOUD_NAME/API_KEY/API_SECRET, các hàm trả về None/giữ nguyên input
thay vì raise lỗi - caller tự fallback sang lưu file local (xem
app/modules/baby/service.py, app/modules/cry/service.py).
"""
import logging
import os
from typing import Optional

import cloudinary
import cloudinary.uploader

from app.core.config import settings

logger = logging.getLogger(__name__)

_configured = False


def _ensure_configured() -> bool:
    global _configured
    if not (settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET):
        return False
    if not _configured:
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True,
        )
        _configured = True
    return True


def upload_bytes(
    content: bytes,
    folder: str,
    resource_type: str = "auto",
    public_id: Optional[str] = None,
) -> Optional[str]:
    """
    Upload nội dung nhị phân lên Cloudinary.

    Args:
        content: Dữ liệu file (ảnh hoặc audio).
        folder: Thư mục Cloudinary, vd. "babycare/avatars".
        resource_type: "image" cho ảnh, "video" cho audio (Cloudinary gộp audio
            vào pipeline video, không có resource_type "audio" riêng).
        public_id: Tên định danh file trên Cloudinary (không kèm đuôi). Bỏ trống
            để Cloudinary tự sinh ngẫu nhiên.

    Returns:
        secure_url (https) nếu upload thành công, None nếu Cloudinary chưa được
        cấu hình hoặc upload thất bại.
    """
    if not _ensure_configured():
        logger.warning("Cloudinary chưa được cấu hình - bỏ qua upload, dùng lưu trữ local.")
        return None
    try:
        result = cloudinary.uploader.upload(
            content,
            folder=folder,
            resource_type=resource_type,
            public_id=public_id,
            overwrite=True,
        )
        return result.get("secure_url")
    except Exception as e:
        logger.error("Upload Cloudinary thất bại (folder=%s): %s", folder, e)
        return None


def resolve_asset_url(static_path: str, resource_type: str = "video") -> str:
    """
    Với các audio asset có sẵn trong app/static/ (lullaby, white noise, giọng dỗ
    mẫu...), suy ra Cloudinary delivery URL theo quy ước public_id = "babycare" +
    đường dẫn static (bỏ prefix "/static/" và phần mở rộng).

    Nếu chưa cấu hình CLOUDINARY_CLOUD_NAME, trả về nguyên static_path để phục vụ
    từ app/static/ như hiện tại. Nếu đã cấu hình, URL chỉ thực sự tồn tại sau khi
    asset gốc được upload thủ công lên Cloudinary đúng public_id tương ứng.
    """
    if not settings.CLOUDINARY_CLOUD_NAME:
        return static_path

    relative = static_path[len("/static/"):] if static_path.startswith("/static/") else static_path
    public_id_no_ext, ext = os.path.splitext(relative)
    public_id = f"babycare/{public_id_no_ext}"
    format_suffix = f".{ext.lstrip('.')}" if ext else ""
    return f"https://res.cloudinary.com/{settings.CLOUDINARY_CLOUD_NAME}/{resource_type}/upload/{public_id}{format_suffix}"
