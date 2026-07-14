# 🍼 BabyCare AI

## Tổng quan

BabyCare AI là nền tảng web ứng dụng AI hỗ trợ phụ huynh chăm sóc và
theo dõi sức khỏe trẻ sơ sinh.

## Chức năng

### 1. Authentication & User Management

-   Đăng ký/Đăng nhập
-   JWT Authentication
-   Quản lý hồ sơ phụ huynh
-   Phân quyền
-   Đổi/Quên mật khẩu

### 2. Baby Profile

-   Họ tên
-   Ngày sinh
-   Tuổi
-   Chiều cao
-   Cân nặng
-   Nhóm máu
-   Nơi sinh
-   Tiền sử bệnh
-   Ghi chú y tế
-   Bác sĩ theo dõi
-   Quản lý nhiều hồ sơ bé

### 3. AI Chatbot (GraphRAG + LLM)

-   Hỏi đáp chăm sóc trẻ
-   Tư vấn dinh dưỡng
-   Hướng dẫn cho bú
-   Giấc ngủ
-   Chăm sóc hằng ngày
-   Giải thích dấu hiệu bất thường
-   Cá nhân hóa theo hồ sơ
-   Truy xuất tri thức y khoa
-   Không thay thế chẩn đoán bác sĩ

### 4. AI Cry Detection

-   Hungry
-   Burping
-   Belly Pain
-   Discomfort
-   Tired
-   Lonely
-   Cold/Hot
-   Scared
-   Unknown

### 5. Vaccination Management

-   Tự động tạo lịch tiêm
-   Theo dõi đã/chưa tiêm
-   Lịch sử tiêm chủng

### 6. Reminder & Notification

-   Nhắc tiêm chủng
-   Nhắc tái khám
-   Nhắc vitamin
-   Cảnh báo sốt cao
-   Cảnh báo bỏ bú
-   Cảnh báo ngủ bất thường

### 7. Nutrition Recommendation AI

-   Lịch bú
-   Ăn dặm
-   Thực phẩm phù hợp
-   Thực phẩm cần tránh
-   Cá nhân hóa theo tuổi, cân nặng, chiều cao

### 8. Google Calendar Integration

-   Đồng bộ lịch
-   Tiêm chủng
-   Tái khám
-   Theo dõi sức khỏe
-   Nhắc lịch

### 9. Medical Knowledge Base

-   Tài liệu y khoa
-   GraphRAG Knowledge Base
-   Hồ sơ sức khỏe

### 10. Notification System

-   Thông báo lịch tiêm
-   Thông báo lịch khám
-   Nhắc vitamin
-   Cảnh báo sức khỏe

### 11. AI Personalization Engine

-   Cá nhân hóa theo hồ sơ sức khỏe
-   Dùng cho Chatbot, Dinh dưỡng, Nhắc lịch và Cảnh báo

### 12. Dataset Management

-   Donate-a-Cry Corpus

## Kiến trúc chức năng

``` text
BabyCare AI
├── Authentication & User Management
├── Baby Profile
├── AI Chatbot (GraphRAG + LLM)
├── AI Cry Detection
├── Vaccination Management
├── Reminder & Notification
├── Nutrition Recommendation AI
├── Google Calendar Integration
├── Medical Knowledge Base
├── Notification System
├── AI Personalization Engine
└── Dataset Management
```
