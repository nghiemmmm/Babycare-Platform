import re
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# Từ khóa triệu chứng/thắc mắc làm cho câu thành Mixed Query -> Trả về None để nhường cho Tier 1/2
MIXED_QUERY_KEYWORDS = [
    "trớ", "nôn", "có sao không", "tại sao", "có nên", "sao lại",
    "bị sao", "đau", "quấy", "khóc", "mệt", "tư vấn", "làm gì"
]

# Alias STT Mispelling mapping
STT_ALIASES = {
    "hapa coi": "Hapacol",
    "hapa con": "Hapacol",
    "ha pa col": "Hapacol",
    "bép ti mộc": "Aptamil",
    "meo": "ml",
    "em el": "ml",
    "ký rưỡi": ".5 kg",
    "độ 5": ".5 độ",
    "phẩy 5": ".5"
}


class FastTrackingExtractor:
    """
    Tier 0 Fast Extractor (Pure Python Engine):
    - Trích xuất thông số tracking (cữ bú, uống thuốc, chiều cao/cân nặng, nhiệt độ) trong < 5ms.
    - Xử lý các Edge Cases: Mixed Query, Từ địa phương, Lỗi STT, Dải sinh lý.
    """

    @classmethod
    def _normalize_text(cls, text: str) -> str:
        t = text.lower().strip()
        # Chuyển đổi các dạng nói "7 ký rưỡi" -> "7.5 kg", "38 độ 5" -> "38.5 độ"
        t = re.sub(r"(\d+)\s*ký\s*rưỡi", r"\1.5 kg", t)
        t = re.sub(r"(\d+)\s*độ\s*5", r"\1.5 độ", t)
        t = re.sub(r"(\d+)\s*phẩy\s*5", r"\1.5", t)

        for k, v in STT_ALIASES.items():
            t = t.replace(k, v)
        return t

    @classmethod
    def is_mixed_query(cls, text: str) -> bool:
        """Nếu câu chứa câu hỏi hoặc mô tả triệu chứng -> Trả về True để nhường cho Tier 1/2."""
        text_lower = text.lower()
        return any(kw in text_lower for kw in MIXED_QUERY_KEYWORDS)

    @classmethod
    def extract_feeding(cls, text: str) -> Optional[Dict[str, Any]]:
        """Trích xuất cữ bú sữa / ăn dặm."""
        match = re.search(r"(\d+(?:\.\d+)?)\s*(ml|g|gam|muỗng|bình)", text)
        if match:
            amount = float(match.group(1))
            unit = match.group(2)
            if unit == "ml" or unit == "bình":
                food_name = "Sữa công thức" if "sữa" in text else "Sữa mẹ"
            else:
                food_name = "Ăn dặm"

            return {
                "activity_type": "feeding",
                "food_name": food_name,
                "amount_g": int(amount),
                "unit": unit
            }
        # Trường hợp nói tắt: "bú 150", "uống 120"
        short_match = re.search(r"(bú|uống|ăn)\s*(\d+)", text)
        if short_match:
            amount = float(short_match.group(2))
            if 30 <= amount <= 350:  # Dải dung tích bú hợp lý ở trẻ
                return {
                    "activity_type": "feeding",
                    "food_name": "Sữa",
                    "amount_g": int(amount),
                    "unit": "ml"
                }
        return None

    @classmethod
    def extract_medication(cls, text: str) -> Optional[Dict[str, Any]]:
        """Trích xuất nhật ký uống thuốc."""
        t_norm = cls._normalize_text(text)
        t_lower = t_norm.lower()
        med_keywords = ["hapacol", "paracetamol", "thuốc", "uống", "gói", "viên"]
        if not any(k in t_lower for k in med_keywords):
            return None

        med_name = "Hapacol" if "hapacol" in t_lower else "Thuốc hạ sốt"
        dose_match = re.search(r"(\d+(?:\.\d+)?)\s*(mg|ml|gói|viên)", t_lower)
        dosage = f"{dose_match.group(1)}{dose_match.group(2)}" if dose_match else "150mg"

        return {
            "activity_type": "medication",
            "medication_name": med_name,
            "dosage": dosage
        }


    @classmethod
    def extract_growth(cls, text: str) -> Optional[Dict[str, Any]]:
        """Trích xuất chiều cao (cm) & cân nặng (kg) dựa trên dải sinh lý trẻ em."""
        t_norm = cls._normalize_text(text)
        height = None
        weight = None

        # Pattern có đơn vị
        h_match = re.search(r"(\d+(?:\.\d+)?)\s*(cm|phân)", t_norm)
        if h_match:
            height = float(h_match.group(1))

        w_match = re.search(r"(\d+(?:\.\d+)?)\s*(kg|ký|cân)", t_norm)
        if w_match:
            weight = float(w_match.group(1))

        # Phân định theo dải sinh lý nếu thiếu đơn vị
        if not height and not weight:
            numbers = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", t_norm)]
            for num in numbers:
                if 40.0 <= num <= 110.0 and height is None:
                    height = num
                elif 2.0 <= num <= 25.0 and weight is None:
                    weight = num

        if height or weight:
            return {
                "activity_type": "growth",
                "height": height or 65.0,
                "weight": weight or 7.2
            }
        return None


    @classmethod
    def extract_temperature(cls, text: str) -> Optional[Dict[str, Any]]:
        """Trích xuất nhiệt độ sốt (°C)."""
        temp_match = re.search(r"(\d{2}(?:\.\d+)?)\s*(độ|°c|c)", text)
        if temp_match:
            temp = float(temp_match.group(1))
            if 35.0 <= temp <= 42.0:
                return {
                    "activity_type": "symptom",
                    "symptoms": [f"Sốt {temp}°C"],
                    "temperature": temp
                }
        return None

    @classmethod
    def extract_greeting(cls, text: str) -> Optional[Dict[str, Any]]:
        """Bóc tách các câu chào hỏi xã giao đơn giản (Tier 0 Fast Greeting)."""
        t_clean = text.lower().strip()
        t_clean = re.sub(r"[!.,~?:\-=_]+$", "", t_clean).strip()

        greeting_phrases = {
            "hi", "hello", "helo", "hey", "alo", "alô", "chào", "xin chào",
            "chào bạn", "chào bác sĩ", "chào bac si", "chào bot", "chào em",
            "chào mẹ", "chào bé", "good morning", "good afternoon", "good evening"
        }
        if t_clean in greeting_phrases or re.match(r"^(hi|hello|helo|hey|alo|alô|chào|xin chào)\s+(bạn|bác sĩ|bac si|bot|em|mẹ|admin|babycare)?$", t_clean):
            return {"activity_type": "greeting"}
        return None

    @classmethod
    def extract_read_query(cls, text: str) -> Optional[Dict[str, Any]]:
        """Bóc tách các câu hỏi tra cứu thông tin & nhật ký DB gần nhất của bé (Tier 0 Deterministic Read)."""
        if any(k in text for k in ["bú gần nhất", "ăn gần nhất", "cữ bú gần nhất", "mấy giờ bú", "bú lúc mấy giờ"]):
            return {"activity_type": "read_last_feed"}
        if any(k in text for k in ["dùng thuốc gần nhất", "uống thuốc gần nhất", "lần uống thuốc gần nhất"]):
            return {"activity_type": "read_last_medication"}
        if any(k in text for k in ["tổng sữa hôm nay", "hôm nay bú bao nhiêu", "bú được bao nhiêu sữa"]):
            return {"activity_type": "read_today_milk"}
        if any(k in text for k in ["cân nặng", "nặng bao nhiêu", "chiều cao", "cao bao nhiêu", "mấy tháng", "bao nhiêu tháng"]):
            return {"activity_type": "read_growth_profile"}
        return None

    @classmethod
    def try_extract(cls, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Thực hiện trích xuất cấp tốc (Tier 0 Deterministic Read & Fast Greeting).
        Trả về kết quả xác định bằng Pure Code (< 5ms).
        """
        if not user_message or not user_message.strip():
            return None

        # 1. Edge Case: Nếu là Mixed Query (vừa tra cứu vừa thắc mắc/triệu chứng) -> Trả về None để LLM xử lý
        if cls.is_mixed_query(user_message):
            logger.info("[FastTrackingExtractor] Bỏ qua Tier 0 do phát hiện Mixed Query (đưa sang LLM).")
            return None

        normalized = cls._normalize_text(user_message)

        # 2. Tier 0 Greeting Fast-path
        greeting_res = cls.extract_greeting(normalized)
        if greeting_res:
            return greeting_res

        # 3. Tier 0 Deterministic Read
        result = cls.extract_read_query(normalized)
        if result:
            return result

        return None



