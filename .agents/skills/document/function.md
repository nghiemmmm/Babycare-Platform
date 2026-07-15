# Tài liệu Chức năng Hệ thống BabyCare AI (System Features Document)

## I. Nhóm Chức năng Theo dõi Cơ bản (Core Tracking Features)

### 1. Theo dõi Chiều cao và Cân nặng (Growth Tracking)
* **Mục đích:** Theo dõi sát sao sự phát triển thể chất của bé qua từng giai đoạn.
* **Dữ liệu thu thập:**
  * Cân nặng (kg)
  * Chiều cao (cm)
  * Vòng đầu (cm)
* **Giá trị & Trực quan hóa:**
  * Vẽ biểu đồ tăng trưởng trực quan.
  * So sánh tự động với các chỉ số tiêu chuẩn của Tổ chức Y tế Thế giới (WHO).
  * Hỗ trợ phát hiện sớm các dấu hiệu chậm phát triển hoặc tăng cân không bình thường.

### 2. Theo dõi Triệu chứng (Symptom Tracking)
* **Mục đích:** Ghi nhận các dấu hiệu sức khỏe bất thường của bé theo từng ngày để theo dõi diễn biến.
* **Các triệu chứng thường gặp:**
  * Ho, sốt, nôn trớ.
  * Tiêu chảy, táo bón.
  * Phát ban, nổi mẩn đỏ.
* **Giá trị mang lại:**
  * Theo dõi sát sao diễn biến bệnh tình của bé.
  * Phân tích xu hướng và tần suất xuất hiện các vấn đề sức khỏe.
  * Cung cấp dữ liệu lịch sử chính xác để hỗ trợ bác sĩ khi đi khám bệnh.


### 3. Theo dõi Thuốc (Medication Tracking)
* **Mục đích:** Quản lý lịch trình và lịch sử uống thuốc/bổ sung vitamin của bé.
* **Dữ liệu thu thập:**
  * Tên thuốc / Thực phẩm chức năng
  * Liều dùng (ml, giọt, viên...)
  * Thời gian uống (giờ, số lần trong ngày)
  * Người kê đơn (bác sĩ, tự bổ sung)
* **Giá trị mang lại:**
  * Tránh việc quên liều hoặc uống trùng lặp thuốc.
  * Đánh giá hiệu quả của đợt điều trị dựa trên thời gian uống thuốc và tiến triển triệu chứng.

### 4. Theo dõi Ăn dặm (Solid Food Tracking)
* **Mục đích:** Quản lý hành trình bắt đầu làm quen với thức ăn đặc của bé.
* **Dữ liệu thu thập:**
  * Tên thực phẩm dặm (rau củ, cháo, thịt...)
  * Lượng ăn (gram, thìa...)
  * Phản ứng sau khi ăn (thích thú, nôn trớ, dị ứng, đi ngoài...)
* **Giá trị mang lại:**
  * Giúp AI phân tích và phát hiện sớm các tình trạng dị ứng hoặc không dung nạp đối với từng loại thực phẩm cụ thể.

### 5. Đồng bộ Nhiều Người Chăm Sóc (Caregiver Sync)
* **Mục đích:** Cho phép bố, mẹ, ông bà, hoặc người giữ trẻ (babysitter) cùng tham gia ghi nhận và theo dõi một bé.
* **Ví dụ vai trò:**
  * Bố, Mẹ, Ông bà, Nanny.
* **Giá trị mang lại:**
  * Dữ liệu được đồng bộ hóa theo thời gian thực (Real-time Sync).
  * Giúp bàn giao việc chăm sóc bé giữa các thành viên một cách mượt mà mà không lo thiếu sót thông tin (ví dụ: bé đã bú lúc mấy giờ, đã thay tã chưa).

---

## II. Nhóm Chức năng Trí tuệ Nhân tạo (AI Features)

### 1. Nhập liệu Giọng nói (Voice Logging)
* **Mục đích:** Cho phép phụ huynh nhập nhanh các thông số ghi chép bằng giọng nói thay vì bấm tay.
* **Ví dụ câu lệnh:**
  * *"Bé vừa bú bình 120ml lúc 8 giờ sáng."*
  * AI sẽ tự động phân tích ngôn ngữ tự nhiên và tạo bản ghi tương ứng vào hệ thống.
* **Giá trị mang lại:**
  * Tiết kiệm thời gian, cực kỳ hữu ích khi phụ huynh đang bận bế bé hoặc làm việc khác.

### 2. AI Phân tích Dữ liệu (AI Data Intelligence)
* **Mục đích:** Phân tích dữ liệu tổng hợp đã ghi nhận để tìm ra các quy luật sinh hoạt của bé.
* **Cơ chế hoạt động:**
  * AI sẽ liên tục quét và đối chiếu các trường dữ liệu: Dinh dưỡng (Feeding), Giấc ngủ (Sleep), Thay tã (Diaper) và Triệu chứng (Symptoms).
  * Đưa ra các báo cáo sức khỏe và lời khuyên cá nhân hóa.
  * *Ví dụ nhận xét từ AI:*
    > [!NOTE]
    > *"Trong 3 ngày gần đây, lượng bú của bé đã giảm 20% và số lần quấy khóc tăng lên sau mỗi cữ bú. Bạn nên theo dõi thêm các dấu hiệu sốt hoặc đầy hơi."*

### 3. Dự đoán Tiếng khóc của Bé (Baby Cry Prediction)
* **Mục đích:** Dự đoán nguyên nhân khiến bé khóc và hỗ trợ vỗ về bé kịp thời.
* **Các yếu tố AI sử dụng để phân tích:**
  * Âm thanh/Video thu âm trực tiếp tiếng khóc của bé.
  * Dữ liệu ngữ cảnh sinh hoạt: Thời gian thức (wake window), tần suất đi vệ sinh, thời gian cữ bú gần nhất và độ no dự kiến của bé.
* **Giá trị mang lại:**
  * Giúp xác định nhanh lý do khóc: Đói, buồn ngủ, tã ướt, hay bé bị đầy hơi/đau ốm.
  * **Trợ lý "Bà Mẹ Ảo" (AI Voice Cloned Assistant):** Đóng vai trò nhân bản giọng nói (voice clone) ấm áp của người mẹ để phát giọng nói vỗ về bé dựa trên lý do khóc vừa phân tích.

### 4. Phát Nhạc & Âm thanh Tự động (Automated Sound Conditioning)
* **Mục đích:** Tự động phát âm thanh xoa dịu khi phát hiện bé khóc để giúp bé tự bình tĩnh và dễ dàng chìm vào giấc ngủ lại.
* **Phân loại âm thanh hỗ trợ:**

| Loại âm thanh | Đặc điểm & Phân loại | Ví dụ cụ thể |
| :--- | :--- | :--- |
| **Tiếng ồn trắng (White Noise)** | Âm thanh tần số rộng giúp che lấp các tiếng ồn khó chịu xung quanh. | Tiếng quạt gió, tiếng mưa rơi, tiếng sóng biển vỗ. |
| **Tiếng ồn hồng (Pink Noise)** | Âm thanh có tần số cân bằng, êm dịu và tự nhiên hơn tiếng ồn trắng. | Tiếng mưa rơi đều đặn, tiếng suối nước chảy nhẹ. |
| **Nhạc ru (Lullabies)** | Các giai điệu êm ái, nhẹ nhàng và quen thuộc với trẻ nhỏ. | Nhạc ru cổ điển, nhạc không lời (Piano/Music Box). |
| **Giọng nói AI (AI Voice)** | Giọng nói nhân bản (AI Voice) ấm áp của mẹ để dỗ dành bé. | *"Không sao đâu bé yêu, mẹ đây rồi, ngủ ngon nhé..."* |