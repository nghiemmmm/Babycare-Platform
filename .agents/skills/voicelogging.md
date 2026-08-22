# Hướng dẫn Kỹ thuật: Hệ thống Nhập liệu Giọng nói & Quản lý Luồng Hội thoại (Voice Logging Architecture)

Tài liệu này chuẩn hóa toàn bộ kiến trúc **Voice Logging**, cơ chế xác định ranh giới kết thúc lượt nói (**Dynamic Adaptive Endpointing**), kiểm soát bất đồng bộ & chống tranh chấp (**Concurrency & Cancellation Control**), cùng các quy chuẩn an toàn dữ liệu nhi khoa (**Pediatric Data Integrity Guardrails**) trong BabyCare AI.

---

## 1. Sơ đồ Kiến trúc Toàn diện (End-to-End Voice Flow)

```
                            Microphone
                                │
                                ▼
                 ┌─────────────────────────────┐
                 │    Web Speech API (vi-VN)   │
                 └──────────────┬──────────────┘
                                │ onresult (interim + final)
                                ▼
                 ┌─────────────────────────────┐
                 │   useSpeechRecognition.ts   │
                 │ • Dynamic Adaptive Timeout  │
                 │   (1200ms vs 2200ms)        │
                 │ • onspeechstart/onspeechend │
                 │ • isSubmittingRef Lock      │
                 └──────────────┬──────────────┘
                                │ onSilence(transcript)
                                ▼
                 ┌─────────────────────────────┐
                 │       DashboardView         │
                 │ • voiceAbortControllerRef   │ ──(Abort in-flight request cũ)
                 │ • voiceRequestEpochRef      │ ──(Chống Stale Overwrite)
                 └──────────────┬──────────────┘
                                │ POST /api/v1/ai/voice-action/parse
                                ▼
                 ┌─────────────────────────────┐
                 │   FastVoiceParser (< 15ms)  │
                 │ • ASR Aliases Correction    │
                 │ • Words-to-Number Converter │
                 │ • Negation & Future Guard   │
                 │ • No Default Drug Fallback  │
                 └──────────────┬──────────────┘
                    ┌───────────┴───────────┐
                    ▼                       ▼
           [Đầy đủ thông số]       [Thiếu thông số]
                    │                       │
                    ▼                       ▼
           Hiển thị Preview      Hiển thị Quick Action Chips
           (1-Tap Confirm)       (Chọn liều/lượng 1 chạm)
                    └───────────┬───────────┘
                                │ Xác nhận
                                ▼
                 ┌─────────────────────────────┐
                 │      Action Dispatcher      │
                 │ • Idempotency Key (MD5)     │
                 │ • Multi-Tool Execution      │
                 │ • Firestore Persistence     │
                 └─────────────────────────────┘
```

---

## 2. Ranh giới Xác định Lượt nói (Dynamic Adaptive Endpointing)

### 2.1. Vấn đề của Fixed Silence Timer
- Nếu đặt thời gian chờ cố định ngắn ($1000\text{ms} \sim 1500\text{ms}$), người dùng nói chậm hoặc ngập ngừng dỗ bé sẽ bị **cắt cụt câu (False Endpoint)**.
- Nếu đặt thời gian chờ quá dài ($> 2500\text{ms}$), hệ thống phản hồi rất trễ sau khi người dùng đã nói xong.

### 2.2. Giải pháp Adaptive Endpointing (`useSpeechRecognition.ts`)
Hệ thống tự động phân tích cấu trúc ngữ pháp thời gian thực của chuỗi `interim transcript`:

| Trạng thái câu nói | Dấu hiệu nhận biết | Thời gian Timeout | Trải nghiệm đạt được |
| :--- | :--- | :---: | :--- |
| **Câu đang mở / Dang dở (Dangling)** | Kết thúc bằng từ nối: *"vừa", "uống", "cho bé", "bú", "ăn", "thuốc"*, hoặc số chưa có đơn vị đo (*"một trăm..."*) | **2200ms** | Cho phụ huynh đủ thời gian ngắt quãng để dỗ bé mà không bị ngắt mic. |
| **Câu đã hoàn chỉnh (Complete)** | Đã có số lượng kèm đơn vị đo (*"150ml", "1 gói", "38.5 độ", "sữa mẹ", "thay tã"*) | **1200ms** | Phản hồi tức thì, mượt mà và giảm độ trễ trải nghiệm. |
| **Câu thông thường khác** | Mặc định | **1500ms** | Cân bằng tự nhiên. |

---

## 3. Kiểm soát Đồng thời & Hủy Yêu cầu Cũ (Concurrency & Cancellation)

Triển khai tại [`frontend/src/components/DashboardView.tsx`](file:///d:/ViT/BABYCARE/babycare-ai/frontend/src/components/DashboardView.tsx):

### 3.1. Hủy Yêu cầu cũ (Request Cancellation)
- Sử dụng `voiceAbortControllerRef` để tự động phát tín hiệu `.abort()` cho request HTTP trước đó ngay khi người dùng bắt đầu nói một câu mới.
- Giải phóng tài nguyên mạng và hủy ngay các tác vụ parse dư thừa trên trình duyệt.

### 3.2. Chống ghi đè kết quả cũ (Stale Overwrite Prevention)
- Sử dụng `voiceRequestEpochRef` (bộ đếm tăng dần):
  ```typescript
  const currentEpoch = ++voiceRequestEpochRef.current;
  const res = await apiFetch(..., { signal: abortController.signal });
  if (currentEpoch !== voiceRequestEpochRef.current) {
    return; // Bỏ qua response cũ nếu đã có request mới hơn được phát đi
  }
  ```
- Đảm bảo khi mạng chập chờn, kết quả của câu nói cũ **không bao giờ đè bẹp** câu nói mới của phụ huynh.

---

## 4. An toàn Dữ liệu Thuốc Nhi khoa (Pediatric Medication Safety)

Triển khai tại [`app/AI_agents/core/fast_voice_parser.py`](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/core/fast_voice_parser.py) và [`app/AI_agents/actions/parser.py`](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/actions/parser.py):

- **Nguyên tắc Tuyệt đối**: **KHÔNG BAO GIỜ tự động gán liều lượng mặc định (Zero Default Guessing)** khi câu nói bị ngắt quãng chỉ có tên thuốc (ví dụ: *"Bé uống Hapacol"*).
- **Quy trình Xử lý**:
  1. Trích xuất `medication_name = "Hapacol 150mg"` hoặc `"Paracetamol"`.
  2. Đánh dấu `dosage = None` và đưa `dosage` vào danh sách `missing_fields`.
  3. Trả về `suggested_chips`: `["80mg", "150mg", "250mg", "5ml", "1 gói", "1/2 gói", "2 giọt", "1 viên"]`.
  4. Giao diện hiển thị Quick Action Chips để phụ huynh chủ động chọn đúng liều lượng chỉ định cho cân nặng của bé.

---

## 5. Phân định: Chống Trùng lặp (Deduplication) vs. Kiểm soát Đồng thời (Concurrency)

| Tiêu chí | Chống Trùng lặp (Deduplication) | Kiểm soát Đồng thời (Concurrency Control) |
| :--- | :--- | :--- |
| **Cơ chế** | MD5 Hash: `MD5(baby_id + action_type + params)` trong `ActionDispatcher` | `AbortController` + `voiceRequestEpochRef` tại Client |
| **Mục đích** | Ngăn phụ huynh vô tình chạm 2 lần vào nút "Xác nhận" gây lưu đúp 2 cữ bú cùng lúc | Ngăn chặn việc câu nói sửa sai *"À sửa lại 180ml"* bị kết quả cũ *"150ml"* đè bẹp |
| **Phạm vi bảo vệ** | Cùng 1 nội dung hành động trong 60 giây | Các câu thoại khác nhau diễn ra liên tiếp trong thời gian thực |
