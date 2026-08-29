# syntax=docker/dockerfile:1.4

# ==============================================================================
# Build Arguments toàn cục
# Cho phép truyền tham số phiên bản Python và Model Version khi build
# ==============================================================================
ARG PYTHON_VERSION=3.11.9-slim
ARG MODEL_VERSION=v1.0.0

# ==============================================================================
# Stage 1: Builder
# Cài đặt công cụ biên dịch và xây dựng virtual environment tối ưu
# ==============================================================================
FROM python:${PYTHON_VERSION} AS builder
ARG MODEL_VERSION

WORKDIR /build

# Cài đặt build dependencies cần thiết cho các thư viện C/C++ (FAISS, soundfile, PyTorch)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libsndfile1-dev \
 && rm -rf /var/lib/apt/lists/*

# Tận dụng triệt để Layer Caching: copy requirements trước khi copy source code
COPY requirements.txt .

# Tạo virtual environment độc lập và cài đặt toàn bộ dependencies
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel \
 && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# Stage 2: Final Runtime
# Image siêu nhẹ cho production, chỉ chứa runtime binaries và virtualenv đã build
# ==============================================================================
FROM python:${PYTHON_VERSION} AS runtime
ARG MODEL_VERSION

WORKDIR /app

# Metadata Label để quản lý image và model version trong hệ thống
LABEL maintainer="BabyCare AI Team"
LABEL ai.model.version="${MODEL_VERSION}"

# Thiết lập các biến môi trường tối ưu cho Python runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH" \
    MODEL_VERSION=${MODEL_VERSION} \
    PORT=8000 \
    HOST=0.0.0.0

# Cài đặt các thư viện hệ thống cần thiết cho AI & Audio (Whisper STT, Soundfile, FAISS OpenMP)
# và curl cho healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libgomp1 \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Tạo dedicated non-root user và group để đảm bảo an toàn bảo mật (UID: 10001)
RUN groupadd -g 10001 appgroup \
 && useradd -u 10001 -g appgroup -s /bin/bash -m -d /home/appuser appuser \
 && mkdir -p /app /home/appuser/.cache \
 && chown -R appuser:appgroup /app /home/appuser

# Copy virtual environment từ builder stage
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

# Copy toàn bộ mã nguồn dự án vào container và phân quyền cho appuser
COPY --chown=appuser:appgroup . /app

# Phân quyền thực thi cho kịch bản tiền khởi động
RUN chmod +x /app/scripts/prestart.sh

# Chuyển sang user không đặc quyền (non-root)
USER appuser

# Expose port backend
EXPOSE 8000

# Healthcheck định kỳ kiểm tra trạng thái dịch vụ FastAPI
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Khởi chạy ứng dụng qua kịch bản tiền khởi động
CMD ["/app/scripts/prestart.sh"]
