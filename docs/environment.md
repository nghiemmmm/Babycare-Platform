# Hướng dẫn Quản lý Môi trường Cấu hình (Environment Management)

Tài liệu này chuẩn hóa quy trình quản lý biến môi trường cho dự án **BabyCare AI**, áp dụng cho Development, Production, Docker và CI/CD.

---

## 1. Cấu trúc các File Môi trường

```text
babycare-ai/
├── .env.example          # Template chuẩn mô tả toàn bộ biến (chứa placeholder, được commit vào Git)
├── .env.development      # Cấu hình cho môi trường phát triển Local / Dev (được gitignore)
├── .env.production       # Cấu hình cho môi trường Production thật (được gitignore)
└── .env                  # File cấu hình đang được ứng dụng nạp trực tiếp (active config)
```

---

## 2. Bảng Phân loại Biến Môi trường

| Nhóm | Biến môi trường | Ý nghĩa / Mặc định |
| :--- | :--- | :--- |
| **Ứng dụng** | `APP_ENV`, `DEBUG`, `PORT`, `HOST`, `FRONTEND_URL` | Chế độ chạy (`development`/`production`), Debug mode, Port máy chủ |
| **Firebase** | `FIREBASE_CREDENTIALS_PATH`, `FIREBASE_WEB_API_KEY` | File Service Account JSON & Web API Key xác thực |
| **Redis** | `REDIS_URL`, `BABY_CACHE_TTL_SECONDS` | Kết nối Redis (Cache thông tin bé, Rate Limiter) |
| **Rate Limit**| `RATE_LIMIT_ENABLED`, `RATE_LIMIT_TRUSTED_PROXIES` | Bật/tắt và cấu hình danh sách IP proxy tin cậy |
| **SMTP Mail** | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | Gửi mã OTP khôi phục mật khẩu qua Email |
| **AI Agents** | `LLM_PROVIDER`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY` | Nhà cung cấp AI và Khóa API xử lý Chat / Khám / Dinh dưỡng |
| **Storage** | `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY` | Lưu trữ ảnh avatar bé và file ghi âm tiếng khóc |
| **Pre-start** | `PRE_START_MAX_TRIES`, `PRE_START_WAIT_SECONDS` | Số lần thử kết nối DB trước khi khởi động server |

---

## 3. Các Lệnh Thao tác Nhanh qua Makefile

### Xem trạng thái môi trường hiện tại:
```bash
make env-status
```
*Lưu ý: Lệnh này an toàn tuyệt đối, ẩn toàn bộ mật khẩu và API keys.*

### Chuyển sang môi trường Development:
```bash
make env-dev
```
- Tự động nạp `.env.development` vào `.env`.
- Bật chế độ `DEBUG=true`, `APP_ENV=development`.

### Chuyển sang môi trường Production:
```bash
make env-prod
```
- Tự động hiển thị cảnh báo an toàn và yêu cầu xác nhận (`y/N`) trước khi nạp `.env.production`.
- Tắt chế độ Debug (`DEBUG=false`), kích hoạt Production Guard.

---

## 4. Nguyên tắc Bảo mật (Security Best Practices)

1. **Tuyệt đối không commit secrets lên Git**: Các file `.env`, `.env.development`, `.env.production` đã được cấu hình chặt chẽ trong `.gitignore`.
2. **Production Guard**: Hệ thống sẽ tự động chặn đứng (raise error) nếu phát hiện khởi động với `APP_ENV=production` nhưng lại bật `DEBUG=true`.
3. **Cơ chế Fail-Open an toàn**: Nếu Redis, SMTP hoặc Cloudinary chưa được cấu hình, hệ thống sẽ tự động fallback sang bộ nhớ / đĩa local mà không làm sập ứng dụng.
