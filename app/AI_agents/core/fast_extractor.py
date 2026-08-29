import re
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta

from app.AI_agents.utils.schemas import FastExtractionData, ActivityTypeEnum
from app.AI_agents.core.constant import MIXED_QUERY_KEYWORDS, STT_ALIASES

logger = logging.getLogger(__name__)


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
    def extract_feeding(cls, text: str) -> Optional[FastExtractionData]:
        """Trích xuất cữ bú sữa / ăn dặm."""
        match = re.search(r"(\d+(?:\.\d+)?)\s*(ml|g|gam|muỗng|bình)", text)
        if match:
            amount = float(match.group(1))
            unit = match.group(2)
            if unit == "ml" or unit == "bình":
                food_name = "Sữa công thức" if "sữa" in text else "Sữa mẹ"
            else:
                food_name = "Ăn dặm"

            return FastExtractionData(
                activity_type=ActivityTypeEnum.FEEDING.value,
                food_name=food_name,
                amount_g=int(amount),
                unit=unit
            )
        # Trường hợp nói tắt: "bú 150", "uống 120"
        short_match = re.search(r"(bú|uống|ăn)\s*(\d+)", text)
        if short_match:
            from app.AI_agents.utils.validators import validate_feeding_amount
            amount = float(short_match.group(2))
            if validate_feeding_amount(amount, unit="ml"):  # Dải dung tích bú hợp lý ở trẻ (30-350ml)
                return FastExtractionData(
                    activity_type=ActivityTypeEnum.FEEDING.value,
                    food_name="Sữa",
                    amount_g=int(amount),
                    unit="ml"
                )
        return None

    @classmethod
    def extract_medication(cls, text: str) -> Optional[FastExtractionData]:
        """Trích xuất nhật ký uống thuốc."""
        t_norm = cls._normalize_text(text)
        t_lower = t_norm.lower()
        med_keywords = ["hapacol", "paracetamol", "thuốc", "uống", "gói", "viên"]
        if not any(k in t_lower for k in med_keywords):
            return None

        med_name = "Hapacol" if "hapacol" in t_lower else "Thuốc hạ sốt"
        dose_match = re.search(r"(\d+(?:\.\d+)?)\s*(mg|ml|gói|viên)", t_lower)
        dosage = f"{dose_match.group(1)}{dose_match.group(2)}" if dose_match else "150mg"

        return FastExtractionData(
            activity_type=ActivityTypeEnum.MEDICATION.value,
            medication_name=med_name,
            dosage=dosage
        )

    @classmethod
    def extract_growth(cls, text: str) -> Optional[FastExtractionData]:
        """Trích xuất chiều cao (cm) & cân nặng (kg) dựa trên dải sinh lý trẻ em."""
        from app.AI_agents.utils.validators import validate_growth_metrics
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
                is_valid_h, _ = validate_growth_metrics(height=num)
                is_valid_w, _ = validate_growth_metrics(weight=num)
                if is_valid_h and height is None:
                    height = num
                elif is_valid_w and weight is None:
                    weight = num

        if height or weight:
            return FastExtractionData(
                activity_type=ActivityTypeEnum.GROWTH.value,
                height=height or 65.0,
                weight=weight or 7.2
            )
        return None

    @classmethod
    def extract_temperature(cls, text: str) -> Optional[FastExtractionData]:
        """Trích xuất nhiệt độ sốt (°C)."""
        from app.AI_agents.utils.validators import validate_temperature
        temp_match = re.search(r"(\d{2}(?:\.\d+)?)\s*(độ|°c|c)", text)
        if temp_match:
            temp = float(temp_match.group(1))
            if validate_temperature(temp):
                return FastExtractionData(
                    activity_type=ActivityTypeEnum.SYMPTOM.value,
                    symptoms=[f"Sốt {temp}°C"],
                    temperature=temp
                )
        return None

    @classmethod
    def extract_greeting(cls, text: str) -> Optional[FastExtractionData]:
        """Bóc tách các câu chào hỏi xã giao đơn giản (Tier 0 Fast Greeting)."""
        t_clean = text.lower().strip()
        t_clean = re.sub(r"[!.,~?:\-=_]+$", "", t_clean).strip()

        greeting_phrases = {
            "hi", "hello", "helo", "hey", "alo", "alô", "chào", "xin chào",
            "chào bạn", "chào bác sĩ", "chào bac si", "chào bot", "chào em",
            "chào mẹ", "chào bé", "good morning", "good afternoon", "good evening"
        }
        if t_clean in greeting_phrases or re.match(r"^(hi|hello|helo|hey|alo|alô|chào|xin chào)\s+(bạn|bác sĩ|bac si|bot|em|mẹ|admin|babycare)?$", t_clean):
            return FastExtractionData(activity_type=ActivityTypeEnum.GREETING.value)
        return None

    @classmethod
    def extract_read_query(cls, text: str) -> Optional[FastExtractionData]:
        """Bóc tách các câu hỏi tra cứu thông tin & nhật ký DB gần nhất của bé (Tier 0 Deterministic Read)."""
        # Nếu chứa câu hỏi mốc phát triển / tập lẫy / ăn dặm / triệu chứng -> nhường luồng cho Tier 1/2
        if any(k in text for k in ["tập lẫy", "tập bò", "tập đi", "ăn dặm", "phát triển", "mốc"]):
            return None

        if any(k in text for k in ["bú gần nhất", "ăn gần nhất", "cữ bú gần nhất", "mấy giờ bú", "bú lúc mấy giờ"]):
            return FastExtractionData(activity_type=ActivityTypeEnum.READ_LAST_FEED.value)
        if any(k in text for k in ["dùng thuốc gần nhất", "uống thuốc gần nhất", "lần uống thuốc gần nhất"]):
            return FastExtractionData(activity_type=ActivityTypeEnum.READ_LAST_MEDICATION.value)
        if any(k in text for k in ["tổng sữa hôm nay", "hôm nay bú bao nhiêu", "bú được bao nhiêu sữa"]):
            return FastExtractionData(activity_type=ActivityTypeEnum.READ_TODAY_MILK.value)
        if any(k in text for k in [
            "cân nặng bao nhiêu", "nặng bao nhiêu", "nặng bao kg", "nặng mấy kg", "bao nhiêu kg",
            "chiều cao bao nhiêu", "cao bao nhiêu", "cao mấy phân", "bao nhiêu cm",
            "cân nặng hiện tại", "chiều cao hiện tại", "cân nặng của bé", "chiều cao của bé",
            "được mấy tháng tuổi", "mấy tháng tuổi rồi", "bao nhiêu tháng tuổi"
        ]):
            return FastExtractionData(activity_type=ActivityTypeEnum.READ_GROWTH_PROFILE.value)
        if any(k in text for k in ["lịch hôm nay", "lịch chăm sóc", "việc hôm nay", "sổ bàn giao", "hôm nay dặn gì", "lịch trình hôm nay"]):
            return FastExtractionData(activity_type=ActivityTypeEnum.READ_CARE_SCHEDULE.value)
        return None

    @classmethod
    def extract_care_schedule_task(cls, text: str) -> Optional[FastExtractionData]:
        """Trích xuất câu lệnh tạo lịch/nhắc việc chăm sóc (Fast Task Creation)."""
        t_lower = text.lower()
        if not any(k in t_lower for k in ["nhắc", "dặn", "đặt lịch", "lên lịch", "hẹn"]):
            return None

        # Tìm mốc giờ (ví dụ: 14h30, 14:30, 2h rưỡi, 3h chiều, 10h)
        time_match = re.search(r"(\d{1,2})[h:](\d{2})?", t_lower)
        scheduled_time = None
        if time_match:
            h = int(time_match.group(1))
            m = int(time_match.group(2)) if time_match.group(2) else 0
            if "chiều" in t_lower and h < 12:
                h += 12
            scheduled_time = f"{h:02d}:{m:02d}"

        # Tìm người phụ trách
        assignee = "Bà nội"
        if "bà ngoại" in t_lower:
            assignee = "Bà ngoại"
        elif "bảo mẫu" in t_lower or "cô" in t_lower:
            assignee = "Bảo mẫu"
        elif "bố" in t_lower:
            assignee = "Bố"
        elif "mẹ" in t_lower:
            assignee = "Mẹ"

        # Tìm loại công việc & dung tích
        amount_match = re.search(r"(\d+)\s*(ml|g|gam)", t_lower)
        amount = int(amount_match.group(1)) if amount_match else None
        unit = amount_match.group(2) if amount_match else "ml"

        task_title = "Cữ chăm sóc bé"
        if "uống thuốc" in t_lower or "hapacol" in t_lower or "vitamin" in t_lower:
            task_title = "Uống thuốc / Vitamin"
        elif "ăn dặm" in t_lower or "cháo" in t_lower or "bột" in t_lower:
            task_title = "Cữ ăn dặm"
            unit = "g"
        elif "bú" in t_lower or "sữa" in t_lower or "uống sữa" in t_lower:
            task_title = "Cữ bú sữa"

        if scheduled_time:
            return FastExtractionData(
                activity_type=ActivityTypeEnum.CREATE_CARE_TASK.value,
                task_title=task_title,
                scheduled_time=scheduled_time,
                assigned_to_name=assignee,
                amount_g=amount,
                unit=unit,
                instructions=text
            )
        return None

    @classmethod
    def try_extract(cls, user_message: str) -> Optional[FastExtractionData]:
        """
        Thực hiện phân tích và bóc tách cấp tốc câu hỏi của người dùng tại Tier 0 bằng Pure Python.

        Chức năng:
            - Nhận diện câu chào hỏi xã giao (Fast Greeting).
            - Nhận diện các câu tra cứu thông số/nhật ký định danh (Deterministic DB Read).
            - Nhận diện tạo lịch/tra cứu sổ bàn giao chăm sóc (Care Coordination Fast-Path).
            - Tự động bỏ qua nếu phát hiện câu hỏi phức tạp (Mixed Query chứa triệu chứng/thắc mắc).

        Args:
            user_message (str): Nội dung văn bản câu hỏi thô gửi từ người dùng.

        Returns:
            Optional[FastExtractionData]: Đối tượng Schema dữ liệu trích xuất (gồm activity_type, các tham số số liệu)
                hoặc None nếu câu hỏi không thuộc diện xử lý Fast-Path của Tier 0.

        Raises:
            Không phát sinh ngoại lệ; tự động trả về None khi gặp chuỗi rỗng hoặc dữ liệu không hợp lệ.
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

        # 3. Tier 0 Care Coordination Task Creation
        task_res = cls.extract_care_schedule_task(normalized)
        if task_res:
            return task_res

        # 4. Tier 0 Deterministic Read
        result = cls.extract_read_query(normalized)
        if result:
            return result

        return None



