---
name: git-branching-mlops
description: "Use when managing Git branching workflows, releases, hotfixes, or feature development for AI/ML engineering teams. Guides branch naming conventions (feature/*, experiment/*, hotfix/*, release/*), PR gates, model validation checkpoints, and semantic versioning. Trigger terms: git branch, branching strategy, gitflow, git workflow, merge PR, release branch, hotfix."
license: MIT
metadata:
  author: BabyCare AI Team
  version: "1.0.0"
  domain: mlops-git
  triggers: git branch, branching strategy, gitflow, git workflow, merge PR, release branch, hotfix, ML branches
  role: specialist
  scope: workflow
  output-format: markdown
---

# Branching Strategy & Git Workflow for AI/ML Teams

Senior MLOps and Git Workflow specialist guiding clean, structured, and reproducible version control for software and machine learning engineering.

---

## 1. Core Branching Model

| Branch | Base From | Merges Into | Purpose & Rules | Protection Level |
|---|---|---|---|---|
| **`main`** *(hoặc `master`)* | — | — | **Mã nguồn Production.** Chứa code và model trọng số đã qua kiểm thử thực tế. Tự động trigger pipeline CD deploy lên môi trường Production. | 🔒 **Protected**: Cấm push trực tiếp. Bắt buộc PR + Code Review + CI pass 100%. |
| **`develop`** | `main` | `main` (qua release) | **Nhánh tích hợp (Integration).** Nơi hội tụ các tính năng mới trước khi đóng gói bản release. Tự động deploy sang môi trường Staging/Dev. | 🔒 **Protected**: Yêu cầu PR từ các nhánh feature/experiment. |
| **`feature/<tên-tính-năng>`** | `develop` | `develop` | Phát triển tính năng mới cho ứng dụng (ví dụ: `feature/add-rag-retrieval`, `feature/whisper-audio-api`). Nhánh ngắn hạn (short-lived). | 🔓 Developer tự do commit & rebase. |
| **`experiment/<tên-thử-nghiệm>`** | `develop` | `develop` *(chỉ khi đạt KPI)* | **Đặc thù AI/ML:** Dành cho việc thử nghiệm mô hình, fine-tune hyperparameters, benchmark kiến trúc mới (ví dụ: `experiment/ast-transformer-tuning`, `experiment/reranker-bge`). | 🔓 Lưu vết toàn bộ metrics & weights. |
| **`release/<phiên-bản>`** | `develop` | `main` & `develop` | Chuẩn bị phát hành phiên bản mới (ví dụ: `release/v1.2.0`). Đóng băng code, nâng số version, cập nhật CHANGELOG, chạy full validation test suite. | 🔒 Sau khi merge vào `main` bắt buộc tạo Git Tag (e.g. `git tag -a v1.2.0`). |
| **`hotfix/<tên-sự-cố>`** | `main` | `main` & `develop` | **Vá lỗi khẩn cấp trên Production.** Sửa lỗi bảo mật, crash nghiêm trọng (ví dụ: `hotfix/firebase-auth-token-crash`). | 🔒 Merge trực tiếp về cả `main` lẫn `develop` để đồng bộ. |

---

## 2. Quy trình & Git Command Cheat Sheet

### 🌿 A. Phát triển tính năng mới (`feature/`)
```bash
# 1. Bắt đầu từ develop mới nhất
git checkout develop
git pull origin develop

# 2. Tạo nhánh feature mới
git checkout -b feature/add-rag-retrieval

# 3. Làm việc, commit và push lên remote
git add .
git commit -m "feat(rag): tích hợp hybrid retrieval và MMR diversity"
git push -u origin feature/add-rag-retrieval

# 4. Tạo Pull Request (PR) từ feature/add-rag-retrieval -> develop trên GitHub
```

---

### 🧪 B. Thử nghiệm Mô hình AI (`experiment/`)
```bash
# 1. Tạo nhánh thử nghiệm từ develop
git checkout -b experiment/cry-ast-model-v2 develop

# 2. Huấn luyện, đánh giá & log kết quả metrics
# ... (Chạy benchmark / validation) ...

# 3. NẾU MÔ HÌNH VƯỢT TRỘI (Đạt KPI độ chính xác / Latency):
# Tạo PR merge vào develop kèm báo cáo benchmark (Eval Report)
# NẾU MÔ HÌNH THẤT BẠI: Đóng nhánh, giữ nguyên commit history trên remote để tra cứu
```

---

### 🏷️ C. Đóng gói & Phát hành bản Release (`release/`)
```bash
# 1. Tạo nhánh release từ develop
git checkout -b release/v1.1.0 develop

# 2. Nâng version trong pyproject.toml / config và cập nhật CHANGELOG.md
git commit -am "chore(release): bump version to 1.1.0"

# 3. Merge vào main và gắn Tag phiên bản
git checkout main
git pull origin main
git merge --no-ff release/v1.1.0
git tag -a v1.1.0 -m "Release version 1.1.0: AST Cry Transformer & RAG Engine"
git push origin main --tags

# 4. Merge ngược lại vào develop để giữ đồng bộ
git checkout develop
git merge --no-ff release/v1.1.0
git push origin develop

# 5. Xóa nhánh release tạm
git branch -d release/v1.1.0
```

---

### 🚨 D. Vá lỗi khẩn cấp Production (`hotfix/`)
```bash
# 1. Xuất phát trực tiếp từ main
git checkout -b hotfix/fix-redis-reconnect main

# 2. Sửa lỗi và test
git commit -am "fix(redis): bổ sung cơ chế retry backoff khi redis timeout"

# 3. Merge vào main + tạo tag bản vá
git checkout main
git merge --no-ff hotfix/fix-redis-reconnect
git tag -a v1.1.1 -m "Hotfix: Fix Redis reconnect issue"
git push origin main --tags

# 4. Merge vào develop
git checkout develop
git merge --no-ff hotfix/fix-redis-reconnect
git push origin develop
```

---

## 3. MLOps Model Validation Gates (Cổng kiểm duyệt AI trong CI/CD)

Trước khi merge bất kỳ PR nào vào `main` hoặc `develop`, bắt buộc vượt qua 4 chặng:

```
[PR Created] 
      ↓
[1. Code Lint & Type Check] (Ruff, MyPy)
      ↓
[2. Automated Unit Tests] (Pytest: API, Auth, Logic)
      ↓
[3. Model Integrity & Architecture Gate] (AST Model tensor shapes, Prompt artifacts)
      ↓
[4. Buildx Container Verification] (Docker build test)
      ↓
[Merged to Main] ──→ Auto Trigger CD Deployment
```

---

## 4. Constraints

### MUST DO
- **MUST** đặt tên nhánh theo đúng tiền tố chuẩn: `feature/`, `experiment/`, `hotfix/`, `release/`.
- **MUST** dùng commit message theo chuẩn Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`).
- **MUST** luôn tạo tag Semantic Versioning (`vMAJOR.MINOR.PATCH`) mỗi khi release lên `main`.
- **MUST** chạy code review và đảm bảo CI pass 100% trước khi bấm Merge PR.

### MUST NOT DO
- **MUST NOT** push code trực tiếp lên `main` hoặc `develop`.
- **MUST NOT** lưu trữ dataset nặng nhiều GBs hoặc weights thô chưa nén vào Git repository (hãy dùng Git LFS, S3 hoặc Volume Mount).
- **MUST NOT** merge nhánh `experiment/` vào `develop` khi chưa có báo cáo benchmark/metrics rõ ràng.
