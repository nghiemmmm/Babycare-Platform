# ==============================================================================
# BABYCARE AI - PROJECT MAKEFILE & TASK RUNNER
# ==============================================================================
# Makefile chuẩn hóa cho quy trình phát triển, kiểm thử, Docker, AI & DevOps
# Sử dụng: make <target> hoặc make help để xem toàn bộ danh sách lệnh
# ==============================================================================

.DEFAULT_GOAL := help

ifeq ($(OS),Windows_NT)
    PYTHON ?= $(if $(wildcard venv/Scripts/python.exe),venv\Scripts\python.exe,python)
    PIP ?= $(if $(wildcard venv/Scripts/pip.exe),venv\Scripts\pip.exe,pip)
else
    PYTHON ?= $(if $(wildcard venv/bin/python),venv/bin/python,python)
    PIP ?= $(if $(wildcard venv/bin/pip),venv/bin/pip,pip)
endif
NPM := npm

# Đường dẫn Docker Compose
DOCKER_DIR := docker
COMPOSE_FILE := $(DOCKER_DIR)/docker-compose.yml
COMPOSE_DEV_FILE := $(DOCKER_DIR)/docker-compose.dev.yml
COMPOSE_PROD_FILE := $(DOCKER_DIR)/docker-compose.prod.yml
COMPOSE_GPU_FILE := $(DOCKER_DIR)/docker-compose.gpu.yml
AIRFLOW_COMPOSE := airflow/airflow_project/docker-compose.yml

# ==============================================================================
# 1. HELP / DOCUMENTATION
# ==============================================================================
.PHONY: help
help: ## Hiển thị hướng dẫn sử dụng và danh sách toàn bộ các lệnh khả dụng
	@echo ========================================================================
	@echo   BabyCare AI - Developer Task Runner
	@echo ========================================================================
	@echo Su dung: make [lenh]
	@echo.
	@$(PYTHON) -c "import sys, re; getattr(sys.stdout, 'reconfigure', lambda **k: None)(encoding='utf-8'); [print(f'  \033[36m{m.group(1):<22}\033[0m {m.group(2)}') for line in open('Makefile', encoding='utf-8') if (m := re.match(r'^([a-zA-Z0-9_-]+):.*?## (.*)$$', line))]"
	@echo.

# ==============================================================================
# 2. ENVIRONMENT MANAGEMENT
# ==============================================================================
.PHONY: env-status env-dev env-prod
env-status: ## Kiểm tra và hiển thị trạng thái cấu hình môi trường hiện tại (.env)
	@$(PYTHON) scripts/switch_env.py status

env-dev: ## Chuyển sang môi trường Development (.env.development -> .env)
	@$(PYTHON) scripts/switch_env.py dev

env-prod: ## Chuyển sang môi trường Production (.env.production -> .env) kèm xác nhận
	@$(PYTHON) scripts/switch_env.py prod

# ==============================================================================
# 3. DEPENDENCIES & SETUP
# ==============================================================================
.PHONY: install install-backend install-frontend setup
install: install-backend install-frontend ## Cài đặt toàn bộ dependencies cho cả Backend và Frontend

install-backend: ## Cài đặt các thư viện Python Backend từ requirements.txt
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt

install-frontend: ## Cài đặt các gói Node.js cho ứng dụng Frontend
	cd frontend && $(NPM) install

setup: install ## Thiết lập môi trường phát triển ban đầu và kiểm tra sức khỏe
	@$(PYTHON) scripts/switch_env.py dev
	@echo "Môi trường đã sẵn sàng!"

# ==============================================================================
# 3. LOCAL DEVELOPMENT
# ==============================================================================
.PHONY: dev dev-backend dev-frontend prestart
dev: dev-backend ## Khởi chạy Backend FastAPI ở chế độ phát triển (Reload tự động)

dev-backend: ## Khởi chạy server FastAPI Backend với Uvicorn reload
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Khởi chạy Frontend React/Vite dev server
	cd frontend && $(NPM) run dev

prestart: ## Chạy kịch bản tiền khởi động kiểm tra kết nối Firestore & Redis
	$(PYTHON) -m app.backend_pre_start

# ==============================================================================
# 4. TESTING & QUALITY ASSURANCE
# ==============================================================================
.PHONY: test test-unit test-integration test-rate-limit test-auth lint lint-frontend build-frontend
test: ## Chạy toàn bộ bộ kiểm thử tự động với Pytest
	$(PYTHON) -m pytest

test-unit: ## Chạy toàn bộ các unit tests
	$(PYTHON) -m pytest tests/unit

test-rate-limit: ## Chạy unit test riêng cho module Rate Limiting
	$(PYTHON) -m pytest tests/unit/test_rate_limit.py -v

test-auth: ## Chạy unit test cho phân hệ Authentication & Firebase
	$(PYTHON) -m pytest tests/unit/test_auth_service.py tests/unit/test_firebase_auth.py -v

lint: ## Kiểm tra cú pháp toàn bộ file Python và type check Frontend
	$(PYTHON) -m py_compile $$(find app tests scripts -name "*.py")
	cd frontend && $(NPM) run lint

lint-frontend: ## Kiểm tra kiểu dữ liệu TypeScript trong thư mục frontend
	cd frontend && $(NPM) run lint

build-frontend: ## Đóng gói production bundle cho Frontend
	cd frontend && $(NPM) run build

# ==============================================================================
# 5. DATABASE & SEEDING (FIREBASE FIRESTORE)
# ==============================================================================
.PHONY: db-check db-seed db-seed-demo
db-check: prestart ## Kiểm tra tính sẵn sàng của kết nối Firebase Firestore & Redis

db-seed: ## Seed toàn bộ dữ liệu người dùng, em bé và nhật ký mẫu vào Firestore
	$(PYTHON) scripts/seed_db.py

db-seed-demo: ## Seed dữ liệu tài khoản demo (Bé Leo, Bé Bo) vào Firestore
	$(PYTHON) scripts/seed_demo_data.py

# ==============================================================================
# 6. AI, AGENTS & DIAGNOSTICS
# ==============================================================================
.PHONY: health-check check-quota benchmark-agents benchmark-rag benchmark-cache download-reranker
health-check: ## Chạy kiểm tra chẩn đoán toàn diện sức khỏe hệ thống và AI Models
	$(PYTHON) scripts/health_check.py

check-quota: ## Kiểm tra hạn mức và trạng thái khả dụng của Gemini API Keys
	$(PYTHON) scripts/check_gemini_quota.py

benchmark-agents: ## Đo lường hiệu năng và thời gian phản hồi của các AI Agents
	$(PYTHON) scripts/benchmark_agents.py

benchmark-rag: ## Benchmark hiệu năng truy vấn Vector RAG và Semantic Search
	$(PYTHON) scripts/benchmark_rag_performance.py

benchmark-cache: ## Benchmark tốc độ và tỉ lệ Cache Hit (LLMOps Cache)
	$(PYTHON) scripts/benchmark_caching.py

download-reranker: ## Tải mô hình AI Reranker mxbai cục bộ cho hệ thống RAG
	$(PYTHON) scripts/download_reranker.py

# ==============================================================================
# 7. ONE-CLICK DEPLOYMENT & CONTAINER ORCHESTRATION
# ==============================================================================
.PHONY: deploy deploy-dev deploy-prod deploy-gpu deploy-all docker-dev docker-prod docker-up docker-up-gpu docker-down docker-logs docker-restart airflow-up airflow-down
deploy: ## Triển khai toàn diện hệ thống một chạm cho Development (Windows)
	powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1 -Env dev

deploy-dev: deploy ## Alias cho make deploy

deploy-prod: ## Triển khai hệ thống một chạm cho Production (kèm xác nhận an toàn)
	powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1 -Env prod

deploy-gpu: ## Triển khai hệ thống một chạm kích hoạt tăng tốc phần cứng GPU
	powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1 -Gpu

deploy-all: ## Triển khai toàn bộ hệ thống bao gồm cả cụm Apache Airflow Pipeline
	powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1 -WithAirflow

docker-dev: ## Khởi chạy cụm Docker Compose cho Development (Hot-Reload, Debug Redis)
	docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) up -d

docker-prod: ## Khởi chạy cụm Docker Compose cho Production (Bảo mật, Resource Limits)
	docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_PROD_FILE) up -d

docker-up: docker-dev ## Khởi chạy Docker cơ bản (mặc định môi trường Dev)

docker-up-gpu: ## Khởi chạy Docker tăng tốc GPU CUDA
	docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) -f $(COMPOSE_GPU_FILE) up -d

docker-down: ## Dừng và gỡ bỏ toàn bộ containers, networks của hệ thống
	docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) down

docker-logs: ## Xem realtime logs của các container
	docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) logs -f

docker-restart: ## Khởi động lại các container
	docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) restart

airflow-up: ## Khởi chạy cụm dịch vụ Apache Airflow Ingestion Pipeline
	docker compose -f $(AIRFLOW_COMPOSE) up -d

airflow-down: ## Dừng cụm dịch vụ Apache Airflow Ingestion Pipeline
	docker compose -f $(AIRFLOW_COMPOSE) down

# ==============================================================================
# 8. CLEANUP & MAINTENANCE
# ==============================================================================
.PHONY: clean clean-pyc clean-cache
clean-pyc: ## Xóa tất cả các file bytecode Python (.pyc, __pycache__)
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-cache: ## Xóa bộ nhớ cache kiểm thử (.pytest_cache)
	rm -rf .pytest_cache 2>/dev/null || true

clean: clean-pyc clean-cache ## Dọn dẹp toàn bộ file rác và bộ nhớ đệm
	@echo "Dọn dẹp hoàn tất!"
