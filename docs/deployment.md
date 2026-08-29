# Hướng dẫn Triển khai Hệ thống (Deployment Guide)

Tài liệu này mô tả kiến trúc và quy trình triển khai tự động hóa "Một Chạm" (**One-Click Deployment**) cho dự án **BabyCare AI Platform** trên Windows (PowerShell) và môi trường Docker.

---

## 1. Kiến trúc Triển khai (Deployment Architecture)

Hệ thống sử dụng mô hình **Compose Overrides Pattern** để phân tách rõ ràng cấu hình giữa các môi trường:

```text
docker/
├── docker-compose.yml          # [Base] Định nghĩa dịch vụ cốt lõi, mạng nội bộ và persistent volumes
├── docker-compose.dev.yml      # [Development] Bật Live-reload, mount mã nguồn, mở port Redis 6379 ra host
├── docker-compose.prod.yml     # [Production] Tắt hot-reload, đóng port Redis, giới hạn RAM/CPU, log limits
└── docker-compose.gpu.yml      # [GPU Override] Cấu hình NVIDIA CUDA 12.1 runtime tăng tốc AI Models
```

---

## 2. Kịch bản Triển khai Tự động One-Click (`scripts/deploy.ps1`)

Kịch bản `deploy.ps1` đóng vai trò là **Deployment Orchestrator** tự động hóa 7 bước:

```text
[Step 0] Preflight Check:
         Kiểm tra Docker Engine, PowerShell, tệp cấu hình .env, models AI cục bộ
[Step 1] Environment Sync:
         Đồng bộ hóa tệp cấu hình môi trường tương ứng (.env.development / .env.production)
[Step 2] Build Docker Images:
         Xây dựng container Image cho Backend API (và Airflow nếu bật)
[Step 3] Start Infrastructure Containers:
         Khởi chạy Backend API & Redis (kèm override môi trường tương ứng)
[Step 4] Readiness Polling Loop:
         Liên tục kiểm tra tính sẵn sàng qua endpoint /health (Tối đa 30 lần, 2s/lần)
[Step 5] Infrastructure & Diagnostics Check:
         Xác nhận kết nối Firebase Firestore và Redis Cache
[Step 6] Optional Re-index:
         Nạp và cập nhật toàn bộ FAISS Vector Index & BM25 Sparse Index (khi truyền -RebuildIndex)
[Step 7] Hybrid Search Verification:
         Gửi truy vấn kiểm thử thực tế và in báo cáo tổng kết trạng thái toàn bộ hệ thống
```

---

## 3. Các Lệnh Triển khai Nhanh qua Makefile

| Lệnh Makefile | Lệnh PowerShell tương đương | Ý nghĩa / Môi trường |
| :--- | :--- | :--- |
| `make deploy` | `.\scripts\deploy.ps1 -Env dev` | Triển khai môi trường Development (mặc định) |
| `make deploy-prod` | `.\scripts\deploy.ps1 -Env prod` | Triển khai môi trường Production (kèm xác nhận an toàn) |
| `make deploy-gpu` | `.\scripts\deploy.ps1 -Gpu` | Triển khai tăng tốc phần cứng NVIDIA GPU CUDA |
| `make deploy-all` | `.\scripts\deploy.ps1 -WithAirflow` | Triển khai toàn bộ hệ thống bao gồm cả Apache Airflow |
| `make docker-dev` | `docker compose -f base -f dev up -d` | Khởi chạy nhanh Docker Dev (Hot-Reload) |
| `make docker-prod` | `docker compose -f base -f prod up -d` | Khởi chạy Docker Production |
| `make docker-down` | `docker compose -f base -f dev down` | Dừng và dọn dẹp các container |

## 4. Hướng dẫn Khởi tạo Máy chủ Mới trên AWS EC2

Khi tạo mới một máy chủ Ubuntu (22.04 / 24.04 LTS) trên AWS EC2, chạy lệnh duy nhất để tự động cài đặt Docker, Swap RAM và Tường lửa UFW:

```bash
# 1. Cấp quyền thực thi và chạy kịch bản bootstrap
chmod +x scripts/ec2-setup.sh
sudo ./scripts/ec2-setup.sh

# 2. Áp dụng nhóm quyền Docker
newgrp docker
```

---

## 5. Bảng Tham số Kịch bản PowerShell

```powershell
.\scripts\deploy.ps1 [-Env <dev|prod>] [-WithAirflow] [-Gpu] [-NoCache] [-RebuildIndex] [-MaxAttempts <30>] [-WaitSeconds <2>]
```

- `-Env dev`: Sử dụng `docker-compose.dev.yml`, bật chế độ Debug và Hot-reload.
- `-Env prod`: Sử dụng `docker-compose.prod.yml`, tắt Debug, kích hoạt Production Guard và bảo mật Redis.
- `-WithAirflow`: Khởi chạy kèm cụm Apache Airflow (Webserver cổng `8080`, Scheduler, Ingestion API).
- `-Gpu`: Sử dụng `docker/docker-compose.gpu.yml` cho máy chủ có card đồ họa NVIDIA.
- `-RebuildIndex`: Tự động nạp lại toàn bộ tri thức y khoa vào FAISS Vector Store sau khi khởi động.
- `-NoCache`: Ép buộc Docker build lại toàn bộ Image từ đầu.

---

## 5. Nguyên tắc Bảo mật trong Triển khai

1. **Không in Credentials / Secrets**: Toàn bộ log và báo cáo tổng kết của script chỉ hiển thị trạng thái `READY / CONFIGURED` hoặc URL mask.
2. **Production Confirmation**: Khi chạy với `-Env prod` và bật `-RebuildIndex`, script yêu cầu người dùng xác nhận `[y/N]` trước khi thực hiện.
3. **Mạng Nội bộ Cách ly**: Trên Production, Redis không mở cổng `6379` ra ngoài máy chủ, chỉ trao đổi qua mạng nội bộ `babycare-net`.
