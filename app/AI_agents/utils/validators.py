import re
import json
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, Tuple, List

logger = logging.getLogger(__name__)


# ── 1. KIỂM THỰC CHUỖI & ĐỊNH DẠNG CƠ BẢN ────────────────────────────────────

def validate_baby_id(baby_id: Optional[str]) -> bool:
    """
    Kiểm tra mã định danh bé có hợp lệ (chuỗi không rỗng) hay không.

    Args:
        baby_id (Optional[str]): Mã định danh bé.

    Returns:
        bool: True nếu baby_id là chuỗi không rỗng, ngược lại False.
    """
    return bool(baby_id and baby_id.strip())


def validate_message_not_empty(message: Optional[str]) -> bool:
    """
    Kiểm tra tin nhắn người dùng có chứa nội dung thực tế hay không.

    Args:
        message (Optional[str]): Nội dung tin nhắn.

    Returns:
        bool: True nếu message có ít nhất 1 ký tự hợp lệ, ngược lại False.
    """
    return bool(message and message.strip())


def validate_audio_file(file_path: Optional[str]) -> bool:
    """
    Kiểm tra định dạng tệp âm thanh có thuộc danh sách hỗ trợ (.wav, .mp3, .ogg, .m4a, .flac).

    Args:
        file_path (Optional[str]): Đường dẫn tệp âm thanh.

    Returns:
        bool: True nếu tệp âm thanh có định dạng hợp lệ, ngược lại False.
    """
    if not file_path:
        return False
    return file_path.lower().endswith((".wav", ".mp3", ".ogg", ".m4a", ".flac", ".webm"))


def validate_iso_date(date_str: Optional[str]) -> bool:
    """
    Kiểm tra chuỗi ngày có tuân thủ đúng định dạng chuẩn ISO (YYYY-MM-DD) hay không.

    Args:
        date_str (Optional[str]): Chuỗi ngày cần kiểm tra.

    Returns:
        bool: True nếu chuỗi ngày hợp lệ, ngược lại False.
    """
    if not date_str or not date_str.strip():
        return False
    try:
        datetime.fromisoformat(date_str[:10])
        return True
    except Exception:
        return False


# ── 2. KIỂM THỰC DẢI SINH LÝ Y KHOA NHI ─────────────────────────────────────

def validate_temperature(temp: float) -> bool:
    """
    Kiểm tra thân nhiệt có nằm trong dải sinh lý người hợp lý (35.0°C đến 42.0°C).

    Args:
        temp (float): Nhiệt độ cơ thể đo được (°C).

    Returns:
        bool: True nếu nằm trong dải sinh lý có thể xảy ra, ngược lại False.
    """
    return 35.0 <= temp <= 42.0


def validate_growth_metrics(
    height: Optional[float] = None,
    weight: Optional[float] = None
) -> Tuple[bool, str]:
    """
    Kiểm tra các chỉ số phát triển thể chất của trẻ em:
    - Chiều cao: 40.0 cm đến 110.0 cm
    - Cân nặng: 2.0 kg đến 25.0 kg

    Args:
        height (Optional[float]): Chiều cao đo được (cm).
        weight (Optional[float]): Cân nặng đo được (kg).

    Returns:
        Tuple[bool, str]: (is_valid, error_reason).
    """
    if height is not None and not (40.0 <= height <= 110.0):
        return False, f"Chiều cao {height}cm nằm ngoài dải sinh lý bình thường (40-110cm)."
    if weight is not None and not (2.0 <= weight <= 25.0):
        return False, f"Cân nặng {weight}kg nằm ngoài dải sinh lý bình thường (2-25kg)."
    return True, "Chỉ số thể chất hợp lệ."


def validate_feeding_amount(amount: float, unit: str = "ml") -> bool:
    """
    Kiểm tra dung tích cữ bú hoặc khẩu phần ăn dặm của trẻ:
    - Sữa (ml/bình): 30ml đến 350ml
    - Ăn dặm (g/gam): 10g đến 500g

    Args:
        amount (float): Số lượng hoặc thể tích.
        unit (str): Đơn vị tính ('ml', 'g', 'bình'...).

    Returns:
        bool: True nếu nằm trong dải khẩu phần hợp lý, ngược lại False.
    """
    if unit in ["ml", "bình"]:
        return 30.0 <= amount <= 350.0
    return 10.0 <= amount <= 500.0


# ── 3. KIỂM THỰC AN TOÀN Y TẾ & CỜ ĐỎ CẤP CỨU ──────────────────────────────

EMERGENCY_SYMPTOM_KEYWORDS = [
    "co giật", "tím tái", "khó thở", "bất tỉnh", "trợn mắt",
    "sốt cao 39", "sốt cao 40", "thở co rút", "li bì", "mất ý thức"
]


def validate_emergency_signals(text: str) -> Tuple[bool, Optional[str]]:
    """
    Kiểm tra xem văn bản có chứa các dấu hiệu cờ đỏ cấp cứu y tế cần can thiệp khẩn cấp hay không.

    Args:
        text (str): Chuỗi câu hỏi hoặc mô tả triệu chứng của phụ huynh.

    Returns:
        Tuple[bool, Optional[str]]: Tuple gồm (is_emergency, detected_signal).
    """
    if not text:
        return False, None
    t_lower = text.lower()
    for kw in EMERGENCY_SYMPTOM_KEYWORDS:
        if kw in t_lower:
            return True, kw
    return False, None


# ── 4. KIỂM THỰC VÀ LÀM SẠCH DỮ LIỆU ĐẦU RA TỪ LLM ─────────────────────────

def validate_and_parse_llm_json(raw_text: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Làm sạch markdown code blocks (```json ... ```) và parse chuỗi JSON từ LLM phản hồi một cách an toàn.

    Args:
        raw_text (str): Chuỗi phản hồi thô từ LLM.

    Returns:
        Tuple[bool, Optional[Dict[str, Any]], str]: (is_success, parsed_dict, error_message).
    """
    if not raw_text or not raw_text.strip():
        return False, None, "Chuỗi JSON đầu vào rỗng."

    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    
    # Tìm kiếm khối JSON bằng regex nếu chuỗi chứa thêm văn bản ngoài
    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group(0)

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return True, data, "Thành công."
        return False, None, f"Dữ liệu parse được không phải dictionary: {type(data)}"
    except json.JSONDecodeError as jde:
        logger.warning(f"[Validator] JSONDecodeError: {jde} | Raw text: {raw_text[:100]}")
        return False, None, f"Lỗi cú pháp JSON: {str(jde)}"
    except Exception as ex:
        logger.error(f"[Validator] Exception parsing JSON: {ex}")
        return False, None, str(ex)
