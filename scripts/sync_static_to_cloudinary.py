"""
Sync Static Assets to Cloudinary
================================
Tự động quét toàn bộ thư mục app/static/ (nhạc ru, tiếng ồn trắng, giọng dỗ mẫu, ảnh)
và tải đồng bộ lên Cloudinary theo đúng cấu trúc thư mục quy ước: `babycare/...`.
"""
import os
import sys
from pathlib import Path

# Đảm bảo import được module app
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import cloudinary
import cloudinary.uploader
from app.core.config import settings

STATIC_DIR = ROOT_DIR / "app" / "static"

# Danh sách các đuôi file được hỗ trợ
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}


def sync_all_static_assets():
    if not (settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET):
        print("❌ LỖI: Chưa cấu hình đầy đủ CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET trong file .env!")
        print("👉 Vui lòng kiểm tra lại file .env trước khi chạy script.")
        return

    print(f"🚀 Bắt đầu kết nối Cloudinary: Cloud Name = '{settings.CLOUDINARY_CLOUD_NAME}'")
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )

    if not STATIC_DIR.exists():
        print(f"⚠️ Thư mục tĩnh {STATIC_DIR} không tồn tại.")
        return

    success_count = 0
    skipped_count = 0
    error_count = 0

    print(f"📂 Đang quét thư mục: {STATIC_DIR}\n" + "=" * 60)

    for root, _, files in os.walk(STATIC_DIR):
        for file in files:
            file_path = Path(root) / file
            ext = file_path.suffix.lower()

            # Xác định resource_type
            if ext in IMAGE_EXTS:
                resource_type = "image"
            elif ext in AUDIO_EXTS:
                resource_type = "video"  # Cloudinary lưu trữ audio qua pipeline video
            else:
                skipped_count += 1
                continue

            # Tính toán đường dẫn tương đối để tạo folder & public_id
            # Ví dụ: app/static/sounds/lullabies/ru_con.mp3 -> babycare/sounds/lullabies/ru_con
            rel_path = file_path.relative_to(STATIC_DIR)
            rel_dir = rel_path.parent
            stem = file_path.stem  # tên file không đuôi

            folder = "babycare" if str(rel_dir) == "." else f"babycare/{str(rel_dir).replace(os.sep, '/')}"
            public_id = stem

            print(f"⬆️  Đang tải: {rel_path} ➡️ [{folder}/{public_id}] ({resource_type})...")

            try:
                cloudinary.uploader.upload(
                    str(file_path),
                    folder=folder,
                    resource_type=resource_type,
                    public_id=public_id,
                    overwrite=True,
                )
                success_count += 1
            except Exception as e:
                print(f"❌ Thất bại khi upload {file_path.name}: {e}")
                error_count += 1

    print("=" * 60)
    print(f"🎉 Hoàn tất đồng bộ!")
    print(f"   - ✅ Thành công: {success_count} file")
    print(f"   - ⏭️ Bỏ qua: {skipped_count} file")
    print(f"   - ❌ Lỗi: {error_count} file")


if __name__ == "__main__":
    sync_all_static_assets()
