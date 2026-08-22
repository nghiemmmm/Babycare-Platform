---
name: docker-ai-best-practices
description: "Use when creating, optimizing, or refactoring Dockerfiles and Docker Compose setups for Python and AI/ML applications. Applies layer caching, multi-stage builds, slim base images, GPU runtime configurations, security best practices (non-root users, secret handling), and clean .dockerignore patterns. Trigger terms: Docker, Dockerfile, docker-compose, containerize, container, image optimization, multi-stage build, .dockerignore."
license: MIT
metadata:
  author: BabyCare AI Team
  version: "1.0.0"
  domain: devops-ai
  triggers: Docker, Dockerfile, docker-compose, containerize, container, image optimization, multi-stage build, .dockerignore, CUDA runtime
  role: specialist
  scope: implementation
  output-format: code
---

# Docker Best Practices for AI & Python Applications

Senior DevOps and Containerization specialist focused on building secure, lightweight, and high-performance Docker images for Python, AI/ML (PyTorch, TensorFlow, CUDA), and FastAPI workloads.

---

## When to Use This Skill

- Writing or optimizing a `Dockerfile` for Python / AI / FastAPI applications.
- Reducing Docker image size (e.g., from 1-2GB+ down to 150-300MB).
- Setting up multi-stage builds for dependency compilation & wheels caching.
- Configuring GPU acceleration (CUDA runtime vs devel).
- Implementing security standards (non-root user, BuildKit secret mounts).
- Creating or tuning `.dockerignore` to prevent context bloat and data leakage.

---

## Core Docker Principles & Best Practices

| # | Principle | Why It Matters | Implementation Rule |
|---|-----------|----------------|---------------------|
| 1 | **Layer Caching** | Dependencies change rarely; code changes often. | `COPY requirements.txt` and run `pip install` **BEFORE** copying source code (`COPY . .`). |
| 2 | **Multi-Stage Builds** | Build tools (`gcc`, `g++`, wheels) are not needed in runtime. | Use a `builder` stage to install/compile, copy only virtualenv/installed packages to the final `slim` image (reduces size by 60–80%). |
| 3 | **.dockerignore** | Large local files bloat build context and leak data. | Exclude `__pycache__`, `.git`, `*.ipynb`, `data/`, `models/`, `.env`, `.venv` from build context. |
| 4 | **Non-Root User** | Running as root creates severe security vulnerabilities. | Create a dedicated unprivileged user (`appuser` with UID 10001) and switch with `USER appuser`. |
| 5 | **COPY vs ADD** | `ADD` has unpredictable magic (remote URL fetch, auto tar extraction). | Always prefer `COPY` over `ADD`. |
| 6 | **Specific Tags** | `:latest` is non-deterministic and can break builds unexpectedly. | Pin exact versions (e.g., `python:3.11.9-slim`, never `python:latest`). |
| 7 | **Secret Handling** | Baking secrets into image layers exposes API keys forever. | Never use `ENV` or `ARG` for secrets. Use BuildKit `--mount=type=secret` or pass via runtime environment variables. |
| 8 | **Slim Base Images & GPU** | Full images contain gigabytes of unnecessary packages. | Use `python:3.11-slim` (~55MB) over `python:3.11` (~900MB). For GPU workloads, prefer `nvidia/cuda:X.Y.Z-runtime` over `-devel`. |

---

## Production Dockerfile Templates

### Template 1: Python / FastAPI Lightweight Multi-Stage Build

```dockerfile
# syntax=docker/dockerfile:1.4

# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.11.9-slim AS builder

WORKDIR /build

# Cài đặt công cụ build cần thiết (nếu có C-extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Tận dụng cache bằng cách copy dependency file trước
COPY requirements.txt .

# Cài đặt package vào virtualenv riêng biệt
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
 && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 2: Final Runtime (Ultra Slim)
# ==========================================
FROM python:3.11.9-slim AS runtime

WORKDIR /app

# Thiết lập biến môi trường tối ưu cho Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Tạo Non-root user để tăng tính bảo mật
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy virtualenv từ stage builder
COPY --from=builder /opt/venv /opt/venv

# Copy source code ứng dụng
COPY --chown=appuser:appgroup . /app

# Chuyển sang user không có quyền root
USER appuser

EXPOSE 8000

# Khởi chạy ứng dụng
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### Template 2: AI / PyTorch with GPU Support

```dockerfile
# syntax=docker/dockerfile:1.4

FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04 AS runtime

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Cài đặt Python runtime tối giản
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3-pip \
    libgomp1 \
 && rm -rf /var/lib/apt/lists/*

# Tạo venv và cài đặt dependencies AI với cờ secret (nếu cần tải model/repo private)
RUN python3.11 -m venv /opt/venv
COPY requirements.txt .
RUN /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
 && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Tạo non-root user
RUN useradd -u 10001 -ms /bin/bash appuser && \
    chown -R appuser:appuser /app

COPY --chown=appuser:appuser . /app
USER appuser

CMD ["python", "server.py"]
```

---

## Standard `.dockerignore` Template

```gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class
*.so

# Git & IDEs
.git/
.gitignore
.gitattributes
.idea/
.vscode/
*.swp
*.swo

# Virtual Environments
.venv/
venv/
ENV/
env/

# Environment files & Secrets
.env
.env.*
*.pem
*.key
credentials.json
serviceAccountKey.json

# Testing & Coverage
.pytest_cache/
.coverage
htmlcov/
tests/

# Large Datasets & Model weights (Mount qua Volume, không build vào Image)
data/
datasets/
models/
*.pt
*.pth
*.onnx
*.bin
*.h5

# Documentation & Scratch
*.md
docs/
scratch/
```

---

## Constraints

### MUST DO
- **MUST** copy `requirements.txt` / `pyproject.toml` and run install before copying app code.
- **MUST** use multi-stage builds when compilation tools (`gcc`, `g++`, `cmake`) are required.
- **MUST** pin specific base image tags (e.g. `python:3.11.9-slim`).
- **MUST** clean apt cache (`rm -rf /var/lib/apt/lists/*`) in the same `RUN` command as `apt-get install`.
- **MUST** run containers with a non-root `USER`.
- **MUST** maintain an up-to-date `.dockerignore`.

### MUST NOT DO
- **MUST NOT** use `:latest` tags in production.
- **MUST NOT** embed API keys, tokens, or `.env` files into Docker images.
- **MUST NOT** bake large model weights (GBs) directly into build layers; use Volumes or Object Storage runtime downloads instead.
- **MUST NOT** use `ADD` when `COPY` suffices.
- **MUST NOT** run containers as `root` in production.
