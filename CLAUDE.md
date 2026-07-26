# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

BabyCare AI is a full-stack baby-care tracking app: a FastAPI backend on Firebase/Firestore, and a React (Vite) frontend served through a small Express proxy. Core features: baby profiles, growth tracking (WHO percentiles), meal/medication/symptom logs, an AI chat agent (LangGraph + Gemini) with cry-sound detection, and weekly reports.

## Commands

### Backend (FastAPI, from repo root)

```bash
python -m venv venv && source venv/bin/activate   # first time
pip install -r requirements.txt

fastapi dev app/main.py        # dev server w/ reload, http://127.0.0.1:8000
# or, to avoid reload restarts when files are written under app/static/ (e.g. avatar uploads):
uvicorn app.main:app --reload --reload-exclude '*.png' --reload-exclude '*.jpg' \
  --reload-exclude '*.jpeg' --reload-exclude '*.webp' --reload-exclude '*.gif'
```

Requires a `.env` in the repo root (see `app/core/settings.py` for every field) with, at minimum, `FIREBASE_CREDENTIALS_PATH` (path to a Firebase service-account JSON) and `FIREBASE_WEB_API_KEY` (Firebase Console → Project Settings → General → Web API Key — different from the service-account key; needed for `/auth/login` and `/auth/refresh`, which call the Identity Toolkit REST API directly rather than the Admin SDK).

Tests (pytest, mocks Firestore via `unittest.mock.patch` on each module's `*Repository` — no live Firebase needed):

```bash
pytest tests/unit/test_baby_profile.py -q          # single file
pytest tests/unit/test_baby_profile.py::test_create_baby -q   # single test
pytest tests/unit -q                                # ⚠️ see gotcha below
```

**Known gotcha:** `tests/unit/test_ai_core.py` fails to *collect* in this environment (`NameError: name 'torch' is not defined`, from a broken `sentence-transformers`/`transformers` chain) and aborts the whole `pytest tests/unit` run. Run other test files individually, or exclude it: `pytest tests/unit --ignore=tests/unit/test_ai_core.py`. Separately, `tests/unit/test_firebase_auth.py::test_get_current_user_missing_credentials` fails whenever `APP_ENV=local` (the auth dependency intentionally bypasses to a mock user in that env — see Auth section below). Both are pre-existing environment issues, not regressions.

### Frontend (React + Vite + Express proxy, from `frontend/`)

```bash
npm install
npm run dev      # starts server.ts (tsx) on :3000 — Vite middleware + API proxy to :8000
npm run lint     # tsc --noEmit
npm run build    # vite build + esbuild-bundles server.ts for production
```

`server.ts` does **not** hot-reload itself (`tsx server.ts`, no `--watch`); after editing it, kill and restart `npm run dev` for changes to take effect. There is no frontend test suite; `npm run lint` (tsc) is the only automated check.

## Architecture

### Two-server dev topology

The frontend is never talking to FastAPI directly. `frontend/server.ts` (Express, port 3000) does three things: serves the Vite dev middleware / SPA, proxies `/api/v1/*` and `/static/*` to `http://127.0.0.1:8000`, and implements one bespoke endpoint (`/api/chat`) that reshapes the backend's AI response shape for the frontend and falls back to a canned reply if Gemini/the backend is unreachable. Because of this proxy hop:

- Any new binary/file-upload endpoint must be forwarded as a raw stream in the generic `/api/v1/*` proxy handler, not `JSON.stringify(req.body)` — `express.json()` only populates `req.body` for `application/json` requests, so multipart bodies come through as `{}`. The proxy branches on `req.is("application/json")` and otherwise forwards `req` itself with `duplex: "half"`.
- The proxy injects `Authorization: Bearer mock-token` on any request that doesn't already have one — see Auth below for what that token does server-side.

### Backend module layout

Each feature lives under `app/modules/<name>/` with a consistent split: `router.py` (FastAPI endpoints, thin), `service.py` (business logic + permission checks), `schemas.py` (Pydantic request/response models), and usually `repository.py` (Firestore access, extends `app.shared.repository.base.BaseRepository`, a small generic CRUD wrapper keyed by collection name + Pydantic model). Routers are wired together in `app/main.py`'s `api_router`, all mounted under `/api/v1`. `app/modules/appointment/` exists but has no router registered in `main.py` — it's unfinished/unused.

Domain errors are plain exception classes in `app/shared/exceptions/__init__.py` (`EntityNotFoundError`, `PermissionDeniedError`, `RateLimitExceededError`, etc.), translated to HTTP responses by handlers registered in `app/core/exception_handler.py`. Prefer raising one of these over a bare `HTTPException` so the response shape (`{"message": ...}`) stays consistent; `HTTPException` is fine for one-off validation (its `{"detail": ...}` shape is also handled by the frontend's error parsing).

### Auth model

Firebase is the identity provider; there's no local password/session table. `register`/`login` call the Firebase Admin SDK / Identity Toolkit REST API directly (`app/modules/auth/service.py`) rather than issuing app-level JWTs. Every authenticated endpoint depends on `get_current_user` (`app/modules/auth/dependencies.py`), which verifies the `Authorization: Bearer <id_token>` header against Firebase on **every request** (no local session cache) — so a role/permission change takes effect immediately, at the cost of a Firebase call per request. When `APP_ENV=local` and the bearer token is literally `mock-token` (or missing), that dependency returns a hardcoded mock user instead of hitting Firebase — this is what lets the frontend proxy work before a real login exists, but it also means auth-dependent tests behave differently under `APP_ENV=local` (see the pytest gotcha above).

Rate limiting (`app/shared/rate_limit.py`) uses Redis `INCR`/`EXPIRE` if `REDIS_URL` is set, otherwise fails-open to an in-memory per-process counter — meaning in dev, restarting the backend clears rate-limit state.

### Baby profile state

`babies` documents have an `is_active` flag meant to be exclusive per guardian (exactly one active baby at a time, used to pick which baby the frontend dashboard shows). `BabyService._deactivate_other_babies()` enforces this on every create/update/`set_active` call — any new code path that can set `is_active: true` must go through it, or you'll reintroduce the bug where two babies end up simultaneously active and the frontend's `babies.find(b => b.isActive)` silently picks whichever the query happens to return first. On the frontend, never derive "active" by array position (`index === 0`) as a fallback for real data — only fall back to it when *no* baby in the list is actually active (corrupt/legacy data).

`App.tsx` is the single source of truth for all fetched data (babies, measurements, feeds, guardians, chat, etc.) — every child view (`DashboardView`, `GrowthView`, `NutritionView`, ...) is presentational and receives data + mutation callbacks as props; there's no separate state-management library or context beyond `AuthContext`. New features that need backend data generally mean: add a handler in `App.tsx` that calls `apiFetch`, thread it down as a prop.

A first-time account has zero babies; `App.tsx` detects `babies.length === 0` after bootstrap and forces the UI into the "create your first baby" flow in `ProfileView` (other nav tabs are disabled, since they all assume `activeBaby` exists and don't null-check it).

### AI / RAG code: what's live vs. dead

Several AI-related trees exist from earlier iterations; only some are wired up:

- `app/AI_agents/` — **live**. LangGraph-based chat orchestrator used by `app/modules/ai_agent`.
- `app/ai/` — **live**, used by `app/modules/cry` (cry-sound classification) and Whisper-based speech-to-text config in `settings`.
- `app/rag/` and `app/shared/ai/` — **not imported anywhere**; dead/legacy code from a prior RAG approach. Don't assume either is on the request path.
- `app/middleware/` (`jwt.py`, `session.py`) — **not imported anywhere**; leftover from before Firebase auth replaced a JWT-based scheme. The middleware actually registered in `main.py` is `app.core.middleware.RequestLoggingMiddleware`.

### RAG dinh dưỡng (`app/AI_agents/knowledge/`) — dùng chung cho chatbot lẫn tính năng dinh dưỡng AI

Pipeline: `DocumentLoader` (đọc PDF/md từ `documents/{domain}/`, gắn metadata `domain` = tên thư mục con) → `TextSplitter` (`RecursiveCharacterTextSplitter`, chunk_size/overlap đọc từ `AIAgentConfig`) → `GoogleGenerativeAIEmbeddings` (`gemini-embedding-001`, **không phải** `bge-m3`/`sentence-transformers` local nữa) → `FAISS` (lưu tại `app/ai/models/faiss_index/`). `RAGPipeline.retrieve()`/`MedicalRetriever.retrieve_context()` nhận tham số `domain` để filter metadata (tự mở `fetch_k=index.ntotal` khi có filter — xem gotcha bên dưới).

Corpus hiện chia domain: `nutrition_general/` (WHO complementary feeding guide), `allergy_safety/`, `illness_diet/` (2 file này do AI soạn, **chưa qua kiểm duyệt chuyên môn**, có disclaimer trong file — cần bác sĩ/chuyên gia dinh dưỡng rà soát trước khi dùng thật), còn lại (`babycare_document.pdf`, `healthy_document.pdf`, `parenting_guidelines.md`) mặc định domain `general`.

**Gotcha quan trọng**: dù không còn dùng `HuggingFaceEmbeddings`, KHÔNG được gỡ `sentence-transformers` khỏi `requirements.txt` — `langchain_text_splitters/__init__.py` tự `import sentence_transformers` ở module-level để export `SentenceTransformersTokenTextSplitter`, thiếu package này sẽ crash ngay cả bước split văn bản, không liên quan gì đến embedding. `requirements.txt` đã ghim `numpy>=1.24.0,<2.0.0` và `sentence-transformers>=3.0.0,<4.0.0` — đừng nới lỏng lại 2 dòng này, bản không ghim từng gây `torch`/`numpy` ABI crash toàn app lúc import (`app.modules.ai_agent` import eager `nutrition_graph.py` → `MedicalRetriever` ngay ở module-level).

Script tiện ích: `python -m app.AI_agents.knowledge.rebuild_index` (xoá + build lại index từ toàn bộ `documents/`), `python -m app.AI_agents.knowledge.eval_retrieval` (chạy câu hỏi mẫu, kiểm tra nguồn kỳ vọng có trong top-k).

### Gợi ý dinh dưỡng AI & Thực đơn 7 ngày (`app/modules/nutrition/ai_recommender.py`)

`NutritionRecommenderService` — gom dữ liệu bé (`allergies`, `health_records` 14 ngày gần nhất coi là "bệnh đang mắc", `solid_food_logs`, `growth_logs`, `medication_logs`) + RAG (2-3 query có domain filter) → prompt Gemini ép JSON → cache Firestore `babies/{id}/nutrition_recommendations/latest`. Endpoint: `GET/POST /api/v1/nutrition/recommendation[/generate]`.

`WeeklyMealPlanService(NutritionRecommenderService)` — kế thừa để tái dùng helper gom dữ liệu, khác ở: 5 query RAG theo nhóm thực phẩm (đạm/rau củ/tinh bột/cần tránh/allergy_safety, k=4 — cần nhiều query hơn vì corpus `nutrition_general` mỏng, 1 query k=3 dễ lặp món trong 28 slot), output 7 ngày × 4 bữa (`sáng/trưa/tối/phụ`) neo theo ngày thật (`date.today()`, server tự tính). Có state machine `status: pending → accepted`: vừa generate → `pending` (xem/chấp nhận/tạo lại tự do); sau `accept` → khoá tạo mới cho tới khi qua `end_date` (7 ngày), gọi `generate` lúc đang khoá → `409 MealPlanLockedError`. Cache Firestore `babies/{id}/weekly_meal_plans/latest`. Endpoint: `GET/POST /api/v1/nutrition/meal-plan/weekly[/generate|/accept]`.

Cả 2 service dùng `retriever`/`reasoner` là `@property` lazy-init (không được eager-construct trong `__init__` vì cả hai được khởi tạo dạng singleton module-level trong `router.py` — chạm `GEMINI_API_KEY`/FAISS lúc import sẽ crash app khi thiếu key, kể cả với request không liên quan).

### Static/uploaded assets

`app/static/` is mounted at `/static` and contains both committed seed images (`img/leo.png`, `img/bo.png`) and runtime-uploaded avatars (`img/avatars/`, gitignored, created on demand by `BabyService.save_avatar`). The upload endpoint (`POST /api/v1/babies/upload-avatar`) generates a random filename server-side rather than trusting the client's filename, and is deliberately separate from create/update-baby because avatar upload can happen before a baby exists (no `baby_id` yet).

## Nhật ký tiến độ

### Dinh dưỡng AI (RAG) — Gợi ý dinh dưỡng + Thực đơn 7 ngày ✅ HOÀN THÀNH (chưa merge/deploy)

**Ngày:** 2026-07-23 | **Nhánh:** `agent`

#### Đã hoàn thành

| Hạng mục | Chi tiết |
|---|---|
| Cấu trúc hoá `baby.allergies` | `str` → `list[str]`, `field_validator(mode="before")` tương thích ngược (đọc string cũ tự tách dấu phẩy) — không cần migrate Firestore |
| Fix bug `create_baby()` | Trước đó bỏ sót `blood_type`/`pediatrician_name`/`allergies` khi tạo bé mới, đã bổ sung |
| Gợi ý dinh dưỡng AI | `NutritionRecommenderService` — RAG + Gemini, cache `nutrition_recommendations/latest`, endpoint `GET/POST /nutrition/recommendation[/generate]` |
| Nâng cấp RAG | Chuyển embedding sang Gemini Embedding API (bỏ `bge-m3` local); tổ chức corpus theo domain (`nutrition_general`/`allergy_safety`/`illness_diet`/`general`); filter theo domain trong FAISS; script `rebuild_index.py` + `eval_retrieval.py` |
| Thực đơn 7 ngày AI | `WeeklyMealPlanService` (kế thừa service trên) — state machine `pending → accepted`, khoá tạo mới 7 ngày sau khi chấp nhận, hỗ trợ `feedback` khi tạo lại, endpoint `GET/POST /nutrition/meal-plan/weekly[/generate\|/accept]` |
| Frontend | `ProfileView.tsx` (tag-input allergies), `NutritionView.tsx` (2 widget mới: gợi ý dinh dưỡng + lịch 7 ngày có modal feedback), `App.tsx` wiring đầy đủ |

#### Trạng thái hiện tại từng phần

| Phần | Trạng thái |
|---|---|
| Migrate `allergies` | ✅ Verify thật trên Firestore (baby "Leo") |
| Gợi ý dinh dưỡng ngắn | ✅ Verify thật end-to-end (Gemini thật, ~1.5k token/lần) |
| Thực đơn 7 ngày | ✅ Verify thật end-to-end — generate/accept/khoá 409 đều test bằng dữ liệu thật (~4.7k token/lần) |
| RAG index | ⚠️ Chỉ 3/4 domain đã build thật (`nutrition_general`+`allergy_safety`+`illness_diet` = 633 vector). Domain `general` (2 PDF WHO, ~2851 chunk) **chưa build** — free tier Gemini Embedding giới hạn 100 request/phút, build hết cần ~35 phút |
| Nội dung `allergy_safety`/`illness_diet` | ⚠️ Do AI soạn, **chưa qua kiểm duyệt chuyên môn** — có disclaimer trong file nhưng cần bác sĩ/chuyên gia dinh dưỡng rà soát trước khi dùng cho người dùng thật |
| `requirements.txt` | ✅ Đã ghim `numpy<2.0.0`, `sentence-transformers<4.0.0` (tránh lặp lại crash torch/numpy ABI đã gặp) |
| Test tự động | ❌ Chưa có unit test cho 2 service mới — mới chỉ verify qua gọi API thật thủ công |

#### Bước tiếp theo

- [ ] Build nốt domain `general` vào FAISS index nếu muốn chatbot chung (`health_graph.py`, `nutrition_graph.py` cũ) cũng hưởng lợi từ corpus mới — cần thời gian chờ do giới hạn quota free tier, hoặc nâng cấp gói trả phí Gemini
- [ ] Nhờ chuyên gia dinh dưỡng/bác sĩ nhi rà soát `documents/allergy_safety/di_ung_thuc_pham_pho_bien.md` và `documents/illness_diet/dinh_duong_khi_om.md` trước khi để người dùng thật thấy
- [ ] Thêm unit test cho `NutritionRecommenderService`/`WeeklyMealPlanService` (mock `AIReasoner`/`MedicalRetriever` như `tests/unit/test_ai_core.py` đã làm cho `KnowledgeRetrievalTool`)
- [ ] Cân nhắc thêm endpoint xem lịch sử thực đơn cũ nếu sản phẩm cần (hiện chỉ giữ bản `latest`, không có lịch sử)
- [ ] Dọn nợ kỹ thuật: hợp nhất 2 lớp Gemini client trùng lặp (`AIReasoner` và `LLMFactory`)
- [ ] Merge nhánh `agent` → `main`

#### Quyết định quan trọng & lý do

| Quyết định | Lý do |
|---|---|
| Đổi `allergies` bằng `field_validator(mode="before")` thay vì script migrate | Không có sẵn cơ chế migrate Firestore trong codebase; validator đọc-tương-thích-ngược an toàn hơn, tự nâng cấp dữ liệu cũ khi đọc mà không cần rewrite hàng loạt document |
| Chuyển embedding sang Gemini Embedding API, bỏ `bge-m3` local | `bge-m3` qua `sentence-transformers` cần tải model ~2GB + phụ thuộc `torch` — đã tự tay gặp và debug crash toàn app do xung đột phiên bản `torch`/`numpy`/`transformers` |
| Vẫn giữ `sentence-transformers` trong `requirements.txt` dù không dùng `HuggingFaceEmbeddings` nữa | `langchain_text_splitters` tự import `sentence_transformers` ở module-level để export `SentenceTransformersTokenTextSplitter` — gỡ package sẽ crash cả bước split văn bản, không liên quan gì đến embedding |
| Mở `fetch_k=index.ntotal` khi có domain filter | FAISS mặc định chỉ lọc metadata trong 20 candidate gần nhất trước khi filter — domain nhỏ (10-21 chunk/3484 tổng) gần như luôn bị bỏ sót nếu không mở rộng phạm vi tìm trước (bug thật đã phát hiện + sửa lúc verify) |
| Cache 1 document `"latest"` (ghi đè) thay vì lưu lịch sử nhiều bản | Đây là "gợi ý/thực đơn hiện tại", không phải audit log — tránh gọi lại RAG+Gemini tốn token (~1.5-4.7k/lần) mỗi lần user mở tab |
| `WeeklyMealPlanService` kế thừa `NutritionRecommenderService` | Tái dùng nguyên các helper gom dữ liệu bé (`_get_active_conditions`, `_get_averse_ingredients`, `_calculate_age_months`, lazy `retriever`/`reasoner`) đã có, tránh copy-paste logic |
| 5 query RAG (theo nhóm thực phẩm) cho thực đơn 7 ngày thay vì 1 query như gợi ý ngắn | Corpus `nutrition_general` chỉ có 1 tài liệu (602 chunk) — 28 món/tuần dễ lặp nếu chỉ dùng 1 query k=3; nhiều query theo chủ đề lấy được nhiều chunk đa dạng hơn cho 1 lần sinh |
| State machine `pending → accepted` + khoá 7 ngày sau khi chấp nhận | Theo yêu cầu người dùng: cho xem trước/tạo lại thoải mái khi chưa chấp nhận, khoá sau khi chấp nhận để tránh đổi thực đơn liên tục giữa tuần đang dùng |
| Cho phép nhập `feedback` tự do khi "Tạo lại" (chưa accept) | Theo yêu cầu người dùng — AI điều chỉnh thực đơn mới theo phản hồi (vd "bé không thích cá") thay vì chỉ random lại |
