# Tài liệu Đặc tả API Endpoints - Hệ thống BabyCare AI

Tài liệu này liệt kê toàn bộ các API Endpoints cần thiết để phục vụ các chức năng giao diện của ứng dụng BabyCare AI. Các API được thiết kế theo chuẩn RESTful và sử dụng định dạng JSON cho dữ liệu gửi/nhận.

---

## 1. Trang Dashboard (Bảng điều khiển tổng quan)
Phục vụ hiển thị nhanh các trạng thái trong ngày của bé hiện tại.

### 1.1. Lấy thông tin tổng quan trong ngày
* **HTTP Method**: `GET`
* **Endpoint**: `/api/v1/dashboard/summary`
* **Tham số**:
  * `baby_id` (Query String, String, Bắt buộc): ID của bé đang active.
* **Dữ liệu trả về (Response)**:
  ```json
  {
    "milk_intake": { "current": 360, "target": 800, "unit": "ml" },
    "sleep_duration": { "current": 240, "target": 720, "unit": "mins" },
    "diaper_changes": { "current": 3, "target": 6 },
    "medications_due": 1,
    "last_feed_time": "10:30 AM",
    "nap_timer_running": false
  }
  ```

### 1.2. Lấy gợi ý hàng ngày từ AI (AI Tip of the Day)
* **HTTP Method**: `GET`
* **Endpoint**: `/api/v1/dashboard/ai-tip`
* **Tham số**:
  * `baby_id` (Query String, String, Bắt buộc): ID của bé.
* **Dữ liệu trả về (Response)**:
  ```json
  {
    "tip_id": "tip_102",
    "category": "Sleep Guidance",
    "content": "Liam đã có giấc ngủ ngắn chất lượng lúc 10h sáng. Khoảng thời gian tỉnh táo tiếp theo phù hợp là 2.5 tiếng trước giấc ngủ trưa.",
    "scientific_reference": "National Sleep Foundation guidelines (4-12 months)"
  }
  ```

---

## 2. Trang Baby Profile & Caregiver Sync (Hồ sơ của Bé & Kết nối người chăm sóc)
Quản lý nhân khẩu học của bé và vòng tròn chia sẻ chăm sóc gia đình.

### 2.1. Lấy danh sách bé trong tài khoản gia đình
* **HTTP Method**: `GET`
* **Endpoint**: `/api/v1/babies`
* **Dữ liệu trả về (Response)**:
  ```json
  [
    {
      "id": "baby_01",
      "name": "Liam James",
      "birth_date": "2026-01-05",
      "gender": "Boy",
      "avatar_url": "https://images.unsplash.com/.../photo.jpg",
      "is_active": true
    }
  ]
  ```

### 2.2. Đăng ký hồ sơ bé mới (Add Baby)
* **HTTP Method**: `POST`
* **Endpoint**: `/api/v1/babies`
* **Dữ liệu gửi lên (Request Body)**:
  ```json
  {
    "name": "Liam James",
    "birth_date": "2026-01-05",
    "gender": "Boy",
    "avatar_url": "https://images.unsplash.com/.../photo.jpg"
  }
  ```
* **Dữ liệu trả về (Response)**:
  ```json
  {
    "success": true,
    "baby": {
      "id": "baby_02",
      "name": "Liam James",
      "birth_date": "2026-01-05",
      "gender": "Boy",
      "avatar_url": "https://images.unsplash.com/.../photo.jpg",
      "is_active": true
    }
  }
  ```

### 2.3. Cập nhật hồ sơ bé hiện tại
* **HTTP Method**: `PUT`
* **Endpoint**: `/api/v1/babies/{baby_id}`
* **Tham số đường dẫn**: `baby_id` (String) - ID của bé cần cập nhật.
* **Dữ liệu gửi lên (Request Body)**:
  ```json
  {
    "name": "Liam James Updated",
    "birth_date": "2026-01-05",
    "gender": "Boy",
    "avatar_url": "https://images.unsplash.com/.../photo.jpg"
  }
  ```
* **Dữ liệu trả về (Response)**:
  ```json
  {
    "success": true,
    "message": "Baby profile updated successfully"
  }
  ```

### 2.4. Lấy danh sách những người chăm sóc (Caregivers Circle)
* **HTTP Method**: `GET`
* **Endpoint**: `/api/v1/guardians`
* **Dữ liệu trả về (Response)**:
  ```json
  [
    {
      "id": "g_01",
      "name": "Elena",
      "email": "mom@family.com",
      "role": "ADMIN",
      "status": "Synced"
    },
    {
      "id": "g_02",
      "name": "David",
      "email": "dad@family.com",
      "role": "GUARDIAN",
      "status": "Synced"
    }
  ]
  ```

### 2.5. Mời thành viên gia đình chăm sóc mới (Invite Member)
* **HTTP Method**: `POST`
* **Endpoint**: `/api/v1/guardians/invite`
* **Dữ liệu gửi lên (Request Body)**:
  ```json
  {
    "name": "Grandma Martha",
    "email": "martha@grandma.com",
    "role": "VIEWER"
  }
  ```
* **Dữ liệu trả về (Response)**:
  ```json
  {
    "success": true,
    "message": "Invitation email dispatched successfully",
    "invitation_id": "invite_9043"
  }
  ```

### 2.6. Xóa quyền truy cập của một người chăm sóc
* **HTTP Method**: `DELETE`
* **Endpoint**: `/api/v1/guardians/{guardian_id}`
* **Tham số đường dẫn**: `guardian_id` (String) - ID người chăm sóc cần xóa.
* **Dữ liệu trả về (Response)**:
  ```json
  {
    "success": true,
    "message": "Caregiver removed from family circle"
  }
  ```

### 2.7. Lấy lịch sử dòng hoạt động thời gian thực (Real-time Activity Stream)
* **HTTP Method**: `GET`
* **Endpoint**: `/api/v1/activities/stream`
* **Tham số**:
  * `baby_id` (Query String, String, Bắt buộc): ID của bé.
  * `limit` (Query String, Integer, Mặc định: 10): Số lượng bản ghi hoạt động muốn lấy.
* **Dữ liệu trả về (Response)**:
  ```json
  [
    { "user": "Elena (Mom)", "action": "logged formula feeding 180ml", "time": "5 mins ago", "type": "feeding" },
    { "user": "David (Dad)", "action": "started nap sleep timer", "time": "20 mins ago", "type": "sleep" }
  ]
  ```

---

## 3. Trang Advanced AI Assistant (Trợ lý AI Chuyên sâu)
Trung tâm chat thông minh kết hợp trích xuất tự động.

### 3.1. Lấy danh sách lịch sử cuộc chat (Recent Chats List)
* **HTTP Method**: `GET`
* **Endpoint**: `/api/v1/ai/threads`
* **Dữ liệu trả về (Response)**:
  ```json
  [
    { "id": "thread_01", "title": "Baby Bo's Sitting Progress", "last_updated": "2026-07-18T10:11:00" },
    { "id": "thread_02", "title": "Fever Dose at 101.8°F", "last_updated": "2026-07-17T18:00:00" }
  ]
  ```

### 3.2. Bắt đầu phiên chat mới
* **HTTP Method**: `POST`
* **Endpoint**: `/api/v1/ai/threads`
* **Dữ liệu trả về (Response)**:
  ```json
  {
    "thread_id": "thread_03",
    "title": "New Chat Session"
  }
  ```

### 3.3. Gửi tin nhắn chat và nhận phản hồi AI
* **HTTP Method**: `POST`
* **Endpoint**: `/api/v1/ai/threads/{thread_id}/messages`
* **Tham số đường dẫn**: `thread_id` (String) - ID phiên chat hiện tại.
* **Dữ liệu gửi lên (Request Body)**:
  ```json
  {
    "content": "Bo vừa bú một bình sữa công thức 150ml lúc 12:00 trưa.",
    "type": "text" 
  }
  ```
  *(Đối với ghi âm giọng nói, `type` sẽ là `"audio"` kèm đường dẫn file nhị phân / base64).*
* **Dữ liệu trả về (Response)**:
  ```json
  {
    "ai_response": {
      "content": "Tôi ghi nhận Bo đã bú 150ml sữa. Tôi đã chuẩn bị một Feeding Log gợi ý ở cột bên phải để bạn xác nhận.",
      "citations": [
        { "title": "WHO Fluid Intake Guideline", "uri": "https://who.int/nutrition" }
      ]
    },
    "extracted_logs": [
      {
        "type": "feeding",
        "title": "Feeding Log",
        "detail": "150ml Formula",
        "value": 150,
        "time": "12:00 PM"
      }
    ]
  }
  ```

### 3.4. Bấm giờ ngủ của bé (Nap Stopwatch Trigger)
* **HTTP Method**: `POST`
* **Endpoint**: `/api/v1/ai/sleep/timer`
* **Dữ liệu gửi lên (Request Body)**:
  ```json
  {
    "baby_id": "baby_01",
    "action": "start" // "start" để bắt đầu đếm, "stop" để dừng và lưu log
  }
  ```
* **Dữ liệu trả về (Response)**:
  ```json
  {
    "success": true,
    "status": "Running",
    "start_time": "2026-07-18T10:25:00Z"
  }
  ```

---

## 4. Trang Nutrition & Solid Food AI (Dinh dưỡng & Ăn dặm AI)
Nhật ký nguyên liệu ăn dặm, sữa và theo dõi phản ứng của bé.

### 4.1. Lấy lịch sử bú sữa và ăn dặm trong ngày
* **HTTP Method**: `GET`
* **Endpoint**: `/api/v1/nutrition/feeds`
* **Tham số**:
  * `baby_id` (Query String, String, Bắt buộc): ID của bé.
  * `date` (Query String, String, Ví dụ: `"Today"` hoặc `"2026-07-18"`): Lọc theo ngày.
* **Dữ liệu trả về (Response)**:
  ```json
  [
    { "id": "feed_01", "type": "Formula", "details": "Formula Milk", "amount": 180, "time": "08:00 AM" },
    { "id": "feed_02", "type": "Solids", "details": "Sweet Potato Purée", "amount": 1, "time": "10:30 AM" }
  ]
  ```

### 4.2. Thêm mới lịch sử ăn uống
* **HTTP Method**: `POST`
* **Endpoint**: `/api/v1/nutrition/feeds`
* **Dữ liệu gửi lên (Request Body)**:
  ```json
  {
    "baby_id": "baby_01",
    "type": "Formula", 
    "details": "Formula Milk",
    "amount": 150,
    "time": "12:00 PM"
  }
  ```
* **Dữ liệu trả về (Response)**:
  ```json
  {
    "success": true,
    "feed_id": "feed_03"
  }
  ```

### 4.3. Xóa một bản ghi ăn uống
* **HTTP Method**: `DELETE`
* **Endpoint**: `/api/v1/nutrition/feeds/{feed_id}`
* **Tham số đường dẫn**: `feed_id` (String) - ID bản ghi cần xóa.
* **Dữ liệu trả về (Response)**:
  ```json
  {
    "success": true,
    "message": "Feed log deleted successfully"
  }
  ```

### 4.4. Lấy danh sách nguyên liệu ăn dặm và phản ứng của bé
* **HTTP Method**: `GET`
* **Endpoint**: `/api/v1/nutrition/ingredients`
* **Tham số**:
  * `baby_id` (Query String, String, Bắt buộc): ID của bé.
* **Dữ liệu trả về (Response)**:
  ```json
  [
    { "id": "ing_01", "name": "Avocado Mash", "reaction": "Loved it", "date": "2026-07-18" },
    { "id": "ing_02", "name": "Peanut Butter", "reaction": "Allergic Reaction", "date": "2026-07-17" }
  ]
  ```

### 4.5. Lưu log phản ứng nguyên liệu ăn dặm mới
* **HTTP Method**: `POST`
* **Endpoint**: `/api/v1/nutrition/ingredients`
* **Dữ liệu gửi lên (Request Body)**:
  ```json
  {
    "baby_id": "baby_01",
    "name": "Spinach Purée",
    "reaction": "Loved it"
  }
  ```
* **Dữ liệu trả về (Response)**:
  ```json
  {
    "success": true,
    "ingredient_log_id": "ing_03"
  }
  ```

### 4.6. Xóa log phản ứng nguyên liệu ăn dặm
* **HTTP Method**: `DELETE`
* **Endpoint**: `/api/v1/nutrition/ingredients/{log_id}`
* **Tham số đường dẫn**: `log_id` (String) - ID bản ghi cần xóa.
* **Dữ liệu trả về (Response)**:
  ```json
  {
    "success": true
  }
  ```

---

## 5. Trang Health & Medication (Sổ Sức khỏe & Thuốc)
Cảnh báo khẩn cấp, liều lượng thuốc an toàn và đếm ngược thời gian thực.

### 5.1. Lấy trạng thái cảnh báo an toàn và danh sách thuốc sắp đến giờ
* **HTTP Method**: `GET`
* **Endpoint**: `/api/v1/health/dashboard`
* **Tham số**:
  * `baby_id` (Query String, String, Bắt buộc): ID của bé.
* **Dữ liệu trả về (Response)**:
  ```json
  {
    "safety_alert": {
      "level": "CRITICAL",
      "message": "Paracetamol (Hạ sốt) uống lúc 08:00 AM. Tuyệt đối không cho uống thêm trước 12:00 PM!"
    },
    "countdown_widget": {
      "medication_name": "Paracetamol 120mg",
      "next_eligible_time": "2026-07-18T12:00:00Z",
      "is_administer_disabled": true
    }
  }
  ```

### 5.2. Log thông tin đã cho bé uống thuốc
* **HTTP Method**: `POST`
* **Endpoint**: `/api/v1/health/medications/administer`
* **Dữ liệu gửi lên (Request Body)**:
  ```json
  {
    "baby_id": "baby_01",
    "medication_name": "Paracetamol 120mg",
    "amount": "1 dose",
    "administered_at": "2026-07-18T12:05:00Z"
  }
  ```
* **Dữ liệu trả về (Response)**:
  ```json
  {
    "success": true,
    "next_scheduled_dosage": "2026-07-18T16:05:00Z",
    "countdown_seconds": 14400
  }
  ```

---

## 6. Trang WHO Growth Charts (Theo dõi Tăng trưởng WHO)
Đối chiếu các thông số thể chất với bách phân vị tiêu chuẩn WHO.

### 6.1. Lấy dữ liệu lịch sử số đo thể chất (Cân nặng, Chiều cao, Vòng đầu)
* **HTTP Method**: `GET`
* **Endpoint**: `/api/v1/growth/measurements`
* **Tham số**:
  * `baby_id` (Query String, String, Bắt buộc): ID của bé.
* **Dữ liệu trả về (Response)**:
  ```json
  [
    { "id": "m_01", "age_months": 5, "weight": 6.8, "height": 64.5, "head_circumference": 41.5, "date": "2026-06-05" },
    { "id": "m_02", "age_months": 6, "weight": 7.2, "height": 66.2, "head_circumference": 42.1, "date": "2026-07-05" }
  ]
  ```

### 6.2. Thêm số đo tăng trưởng mới
* **HTTP Method**: `POST`
* **Endpoint**: `/api/v1/growth/measurements`
* **Dữ liệu gửi lên (Request Body)**:
  ```json
  {
    "baby_id": "baby_01",
    "weight": 7.5,
    "height": 67.0,
    "head_circumference": 42.5,
    "date": "2026-07-18"
  }
  ```
* **Dữ liệu trả về (Response)**:
  ```json
  {
    "success": true,
    "measurement_id": "m_03",
    "percentiles": {
      "weight_percentile": "50th (Normal)",
      "height_percentile": "45th (Normal)",
      "head_percentile": "55th (Normal)"
    }
  }
  ```
