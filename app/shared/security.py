"""
Security & PII Sanitization Module

Tự động ẩn danh các thông tin cá nhân/y tế nhạy cảm (Tên bé, ngày sinh, sđt)
trước khi ghi log tài chính hoặc log hệ thống để đảm bảo tuân thủ PII Safety.
"""
import re

def mask_pii_prompt(text: str) -> str:
    """
    Ẩn danh thông tin PII nhạy cảm trong prompt/message trước khi ghi log:
    - Phân tích và ẩn tên em bé sau các từ khóa "bé", "cháu", "con", "tên"
    - Ẩn định dạng ngày sinh / số điện thoại
    """
    if not text:
        return ""

    sanitized = text

    # 1. Ẩn số điện thoại
    sanitized = re.sub(r'0[3|5|7|8|9]\d{8}', '[PHONE_NUMBER]', sanitized)

    # 2. Ẩn định dạng ngày sinh (dd/mm/yyyy hoặc yyyy-mm-dd)
    sanitized = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '[DOB]', sanitized)

    # 3. Ẩn ngữ cảnh tên em bé: "bé Leo", "cháu Bo", "tên: Minh Anh"
    sanitized = re.sub(r'(?i)\b(bé|cháu|con|tên:?)\s+([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯĂẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴÝỶỸ][a-zàáâãèéêìíòóôõùúăđĩũơưăạảấầẩẫậắằẳẵặẹẻẽềềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]+)', r'\1 [BABY_NAME]', sanitized)

    return sanitized
