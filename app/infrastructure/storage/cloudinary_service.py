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


def delete_asset(public_id_or_url: str, resource_type: Optional[str] = None) -> bool:
    """
    Xóa tài nguyên lưu trữ trên Cloudinary theo public_id hoặc Cloudinary URL.
    Tự động bóc tách public_id từ URL và thử các biến thể đuôi tệp và resource_type.
    """
    if not _ensure_configured() or not public_id_or_url:
        return False

    # 1. Nếu là URL Cloudinary -> Bóc tách public_id và resource_type
    target_id = public_id_or_url
    detected_type = resource_type

    if public_id_or_url.startswith("http://") or public_id_or_url.startswith("https://"):
        try:
            # Ví dụ URL: https://res.cloudinary.com/dtdkqzqvo/raw/upload/v1787680000/babycare/documents/doc_123.pdf
            parts = public_id_or_url.split("/")
            if "upload" in parts:
                idx = parts.index("upload")
                # resource_type nằm trước /upload/ (ví dụ: raw, image, video)
                if idx > 0 and not detected_type:
                    detected_type = parts[idx - 1]
                
                # Phần sau v12345/ chính là public_id
                sub_parts = parts[idx + 1:]
                if sub_parts and sub_parts[0].startswith("v") and sub_parts[0][1:].isdigit():
                    sub_parts = sub_parts[1:]
                target_id = "/".join(sub_parts)
        except Exception as e:
            logger.debug(f"Không thể parse Cloudinary URL: {e}")

    # 2. Thử xóa với các resource_types khác nhau (raw, image) và các biến thể đuôi file
    types_to_try = [detected_type] if detected_type else ["raw", "image", "video"]
    id_variants = [target_id]
    if "." in target_id:
        id_variants.append(os.path.splitext(target_id)[0])
    else:
        id_variants.append(f"{target_id}.pdf")

    success = False
    for rtype in types_to_try:
        for pid in id_variants:
            try:
                res = cloudinary.uploader.destroy(pid, resource_type=rtype, invalidate=True)
                if res.get("result") == "ok":
                    logger.info(f"[Cloudinary] Đã xóa thành công asset {pid} (type={rtype})")
                    success = True
                    break
            except Exception as ex:
                logger.debug(f"[Cloudinary] Thử xóa {pid} ({rtype}) thất bại: {ex}")
        if success:
            break

    # 3. Thử thêm bằng Admin API delete_resources nếu destroy chưa thành công
    if not success:
        try:
            import cloudinary.api
            for rtype in types_to_try:
                del_res = cloudinary.api.delete_resources(id_variants, resource_type=rtype)
                deleted_dict = del_res.get("deleted", {})
                if any(v == "deleted" for v in deleted_dict.values()):
                    logger.info(f"[Cloudinary Admin API] Đã xóa thành công: {deleted_dict}")
                    success = True
                    break
        except Exception as ex_admin:
            logger.debug(f"[Cloudinary Admin API] {ex_admin}")

    return success
