"""
BabyCare AI - Environment Management & Switcher Tool

Provides cross-platform switching and non-sensitive status reporting:
- python scripts/switch_env.py dev
- python scripts/switch_env.py prod [--yes]
- python scripts/switch_env.py status
"""
import os
import shutil
import sys
import argparse
from typing import Dict

# Fix encoding on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_FILE = os.path.join(ROOT_DIR, ".env")
DEV_ENV_FILE = os.path.join(ROOT_DIR, ".env.development")
PROD_ENV_FILE = os.path.join(ROOT_DIR, ".env.production")
EXAMPLE_ENV_FILE = os.path.join(ROOT_DIR, ".env.example")


def parse_env_file(filepath: str) -> Dict[str, str]:
    """Đọc và parse file .env thành dictionary đơn giản mà không dùng thư viện ngoài."""
    env_vars = {}
    if not os.path.exists(filepath):
        return env_vars
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                env_vars[key] = val
    return env_vars


def mask_url_or_secret(val: str) -> str:
    """Ẩn thông tin nhạy cảm trong URL (như Redis password, token)."""
    if not val:
        return "Not Set"
    if "@" in val:
        protocol = val.split("://")[0] if "://" in val else "http"
        host = val.split("@")[-1]
        return f"{protocol}://***@{host}"
    return val


def show_status() -> None:
    """Hiển thị trạng thái môi trường hiện tại một cách trực quan và an toàn."""
    print("\n====================================================")
    print("  👶 BABYCARE AI - ENVIRONMENT STATUS")
    print("====================================================")

    if not os.path.exists(ENV_FILE):
        print("  ⚠️ Trạng thái: Chưa có file .env hoạt động!")
        print(f"  👉 Chạy 'make env-dev' hoặc copy từ .env.example để bắt đầu.\n")
        return

    config = parse_env_file(ENV_FILE)
    app_env = config.get("APP_ENV", "unknown").upper()
    debug_val = config.get("DEBUG", "false").lower() in ("true", "1", "yes")
    port = config.get("PORT", "8000")
    host = config.get("HOST", "0.0.0.0")
    frontend_url = config.get("FRONTEND_URL", "http://localhost:5173")
    llm_provider = config.get("LLM_PROVIDER", "openrouter")
    llm_model = config.get("OPENROUTER_MODEL", "default")
    redis_url = config.get("REDIS_URL", "")
    rate_limit = config.get("RATE_LIMIT_ENABLED", "true")

    has_firebase = bool(config.get("FIREBASE_CREDENTIALS_PATH") or config.get("FIREBASE_CREDENTIALS_JSON"))

    debug_str = "\033[33mENABLED (true)\033[0m" if debug_val else "\033[32mDISABLED (false)\033[0m"
    firebase_str = "\033[32m✅ ĐÃ CẤU HÌNH\033[0m" if has_firebase else "\033[31m❌ THIẾU CREDENTIALS\033[0m"
    redis_str = mask_url_or_secret(redis_url) if redis_url else "In-memory (Fail-open)"
    rate_limit_str = "\033[32mBẬT\033[0m" if rate_limit.lower() == "true" else "\033[33mTẮT\033[0m"
    guard_str = "\033[32mAN TOÀN (Production)\033[0m" if app_env == "PRODUCTION" and not debug_val else "\033[36mDEV MODE (Development)\033[0m"

    print(f"  • Môi trường (APP_ENV)   : \033[36m{app_env}\033[0m")
    print(f"  • Chế độ Debug (DEBUG)    : {debug_str}")
    print(f"  • Máy chủ API (Backend)   : http://{host}:{port}")
    print(f"  • Địa chỉ Frontend        : {frontend_url}")
    print(f"  • Cơ sở dữ liệu Firestore : {firebase_str}")
    print(f"  • Bộ nhớ đệm Redis        : {redis_str}")
    print(f"  • AI Provider / Model     : {llm_provider} ({llm_model})")
    print(f"  • Giới hạn Rate Limiting  : {rate_limit_str}")
    print("----------------------------------------------------")
    print(f"  🛡️ Production Guard       : {guard_str}")
    print("====================================================\n")


def switch_to_dev() -> None:
    """Chuyển sang môi trường Development."""
    if not os.path.exists(DEV_ENV_FILE):
        if os.path.exists(EXAMPLE_ENV_FILE):
            print("Chưa có .env.development, khởi tạo từ .env.example...")
            shutil.copyfile(EXAMPLE_ENV_FILE, DEV_ENV_FILE)
        else:
            print("Lỗi: Không tìm thấy .env.development hoặc .env.example.")
            sys.exit(1)

    shutil.copyfile(DEV_ENV_FILE, ENV_FILE)
    print("✅ Đã chuyển thành công sang môi trường: DEVELOPMENT (.env)")
    show_status()


def switch_to_prod(force: bool = False) -> None:
    """Chuyển sang môi trường Production (với Safety Guard)."""
    if not os.path.exists(PROD_ENV_FILE):
        print(f"❌ Lỗi: Không tìm thấy file {PROD_ENV_FILE}.")
        sys.exit(1)

    if not force:
        print("\n⚠️  CẢNH BÁO AN TOÀN:")
        print("  Bạn đang chuẩn bị chuyển sang môi trường PRODUCTION.")
        print("  Tất cả các API calls và Database sẽ sử dụng cấu hình Production.")
        confirm = input("  Bạn có chắc chắn muốn tiếp tục? (gõ 'y' hoặc 'yes'): ").strip().lower()
        if confirm not in ("y", "yes"):
            print("❌ Đã hủy chuyển môi trường.")
            return

    shutil.copyfile(PROD_ENV_FILE, ENV_FILE)
    print("🚀 Đã chuyển thành công sang môi trường: PRODUCTION (.env)")
    show_status()


def main():
    parser = argparse.ArgumentParser(description="BabyCare AI Environment Switcher")
    subparsers = parser.add_subparsers(dest="command", help="Lệnh thực thi")

    subparsers.add_parser("dev", help="Chuyển sang môi trường Development")
    
    prod_parser = subparsers.add_parser("prod", help="Chuyển sang môi trường Production")
    prod_parser.add_argument("-y", "--yes", action="store_true", help="Bỏ qua xác nhận an toàn")
    
    subparsers.add_parser("status", help="Xem trạng thái cấu hình hiện tại")

    args = parser.parse_args()

    if args.command == "dev":
        switch_to_dev()
    elif args.command == "prod":
        switch_to_prod(force=args.yes)
    elif args.command == "status" or args.command is None:
        show_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
