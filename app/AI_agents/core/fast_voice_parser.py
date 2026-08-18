"""
Fast Voice Parser Module (Deterministic Pure Python Engine)
===========================================================
Engine bóc tách thực thể giọng nói tiếng Việt siêu tốc (< 15ms), 0 Token LLM:
- Hỗ trợ số thập phân dấu phẩy (7,2 kg / 38,5 độ).
- Hỗ trợ chữ số tiếng Việt (một trăm năm mươi, hai trăm mốt, năm chục).
- Hỗ trợ từ địa phương và nói tắt (ký rưỡi, nửa bình, phẩy năm).
- Kiểm tra tính hoàn thiện (Completeness Check) và sinh Quick Chips gợi ý 1-tap.
- Kiểm tra giới hạn y khoa nhi khoa (Pediatric Semantic Guardrails).
- Phát hiện câu phủ định và mốc thời gian tương lai.
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.modules.ai_agent.schemas import VoiceExtractResponse

logger = logging.getLogger(__name__)

# ─── 1. BẢNG MAPPING CHỮ SỐ TIẾNG VIỆT ───────────────────────────────────────
VN_UNITS = {
    "không": 0, "một": 1, "mốt": 1, "hai": 2, "ba": 3, "bốn": 4, "tư": 4,
    "năm": 5, "lăm": 5, "nhỡ": 5, "sáu": 6, "bảy": 7, "bẩy": 7, "tám": 8, "chín": 9, "mười": 10
}

STT_ALIASES = {
    "hapa coi": "hapacol",
    "hapa con": "hapacol",
    "ha pa col": "hapacol",
    "pa ra ce ta mol": "paracetamol",
    "bép ti mộc": "aptamil",
    "meo": "ml",
    "em el": "ml",
    "xăng ti mét": "cm",
    "xentimet": "cm",
    "xen ti mét": "cm",
    "xăng ti": "cm",
    "kí": "kg",
    "ký": "kg",
    "bí đó": "bí đỏ",
    "bí do": "bí đỏ",
    "bí đo": "bí đỏ",
    "ăn bí đó": "ăn bí đỏ",
    "ca rot": "cà rốt",
    "yên mạch": "yến mạch"
}


# Từ khóa triệu chứng hoặc câu hỏi phức tạp (Mixed Query)
MIXED_QUERY_KEYWORDS = [
    "trớ", "nôn", "ọc sữa", "có sao không", "tại sao", "sao lại",
    "bị sao", "đau", "quấy", "khóc thét", "sốt cao", "tư vấn", "làm gì"
]


class FastVoiceParser:
    """
    Bộ bóc tách dữ liệu tiếng Việt Deterministic đạt chuẩn sản xuất.
    """

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Chuẩn hóa văn bản tiếng Việt thô."""
        if not text:
            return ""
        t = text.lower().strip()

        # Thay thế dấu phẩy thập phân "7,2" -> "7.2", "38,5" -> "38.5"
        t = re.sub(r"(\d+),(\d+)", r"\1.\2", t)

        # Chuyển đổi cách nói tắt: "7 ký rưỡi" -> "7.5 kg", "38 độ 5" -> "38.5 độ"
        t = re.sub(r"(\d+)\s*(?:ký|kg|kí)\s*rưỡi", r"\1.5 kg", t)
        t = re.sub(r"(\d+)\s*độ\s*5\b", r"\1.5 độ", t)
        t = re.sub(r"(\d+)\s*phẩy\s*(\d+)", r"\1.\2", t)
        t = re.sub(r"\bnửa bình\b", "90ml", t)
        t = re.sub(r"\bnửa gói\b", "0.5 gói", t)

        # Áp dụng từ điển sửa lỗi ASR
        for k, v in STT_ALIASES.items():
            t = t.replace(k, v)

        return t

    @classmethod
    def convert_vietnamese_words_to_number(cls, text: str) -> str:
        """Chuyển đổi các cụm từ chữ số tiếng Việt cơ bản sang dạng số."""
        # Ví dụ: "một trăm năm mươi" -> "150", "hai trăm" -> "200", "hai trăm mốt" -> "201", "hai trăm mười" -> "210"
        patterns = [
            (r"\bmột trăm năm mươi\b", "150"),
            (r"\bmột trăm hai mươi\b", "120"),
            (r"\bmột trăm tám mươi\b", "180"),
            (r"\bmột trăm\b", "100"),
            (r"\bhai trăm mốt\b", "210"),
            (r"\bhai trăm năm mươi\b", "250"),
            (r"\bhai trăm\b", "200"),
            (r"\bchín mươi\b", "90"),
            (r"\bsáu mươi\b", "60"),
            (r"\bnăm mươi\b", "50"),
            (r"\bnăm chục\b", "50")
        ]
        res = text
        for pat, num_str in patterns:
            res = re.sub(pat, num_str, res)
        return res

    @classmethod
    def detect_negation_or_future(cls, text: str) -> Optional[str]:
        """Phát hiện câu phủ định hoặc hành động ở tương lai."""
        if any(w in text for w in ["chưa ", "không ", "chẳng ", "chưa có"]):
            return "Phát hiện câu phủ định ('chưa/không'). Hệ thống không tự ý ghi nhận hành động này."
        if any(w in text for w in ["tối nay", "ngày mai", "sắp ", "chuẩn bị", "lát nữa"]):
            return "Hành động được nhắc tới trong tương lai. Ba mẹ hãy ghi nhận sau khi bé đã thực hiện nhé."
        return None

    @classmethod
    def parse(cls, transcript: str, baby_id: Optional[str] = None) -> VoiceExtractResponse:
        """
        Thực thi toàn bộ luồng bóc tách dữ liệu từ câu thoại tiếng Việt.
        """
        if not transcript or not transcript.strip():
            return VoiceExtractResponse(
                success=False,
                intent="unknown",
                confidence=0.0,
                warnings=["Câu thoại rỗng, vui lòng nhấn giữ mic và nói lại."],
                confidence_message="Không nhận diện được âm thanh giọng nói."
            )

        norm_text = cls.normalize_text(transcript)
        converted_text = cls.convert_vietnamese_words_to_number(norm_text)

        warnings: List[str] = []
        missing_fields: List[str] = []
        suggested_chips: List[str] = []
        extracted_data: Dict[str, Any] = {}
        canonical_data: Dict[str, Any] = {}
        intent = "unknown"
        confidence = 0.95

        # ── 1. KIỂM TRA PHỦ ĐỊNH HOẶC TƯƠNG LAI ──
        negation_warning = cls.detect_negation_or_future(norm_text)
        if negation_warning:
            warnings.append(negation_warning)
            confidence = 0.40

        # ── 2. PHÂN LOẠI INTENT & BÓC TÁCH THỰC THỂ (ƯU TIÊN MEDICATION TRƯỚC FEEDING) ──

        # A. UỐNG THUỐC (MEDICATION) - Ưu tiên hàng đầu nếu có từ khóa thuốc/siro
        if any(w in converted_text for w in ["thuốc", "hapacol", "paracetamol", "vitamin", "siro", "kháng sinh"]):
            intent = "medication"
            med_name = "Hapacol 150mg"
            if "paracetamol" in converted_text:
                med_name = "Paracetamol"
            elif "vitamin" in converted_text:
                med_name = "Vitamin D3 K2"
            elif "hapacol" in converted_text:
                med_name = "Hapacol 150mg"
            elif "siro" in converted_text:
                med_name = "Siro ho Nhi khoa"

            # Tìm liều lượng: Ưu tiên mg trước, sau đó tới gói, giọt, viên, ml
            mg_match = re.search(r"(\d+(?:\.\d+)?)\s*mg", converted_text)
            dose_match = re.search(r"(\d+(?:\.\d+)?)\s*(giọt|viên|gói|ml)", converted_text)
            dosage_val = None
            
            if mg_match:
                dosage_val = f"{mg_match.group(1)}mg"
            elif dose_match:
                dosage_val = f"{dose_match.group(1)}{dose_match.group(2)}"
            else:
                dosage_val = "150mg" if "hapacol" in converted_text else None

            if dosage_val is not None:
                extracted_data["medication_name"] = med_name
                extracted_data["dosage"] = dosage_val
                canonical_data = {
                    "medication_name": med_name,
                    "dosage": dosage_val
                }
            else:
                missing_fields.append("dosage")
                suggested_chips = ["1 gói", "1/2 gói", "5ml", "2.5ml", "2 giọt", "1 viên"]
                extracted_data["medication_name"] = med_name
                extracted_data["dosage"] = None
                canonical_data = {"medication_name": med_name, "dosage": None}
                confidence = 0.75

        # B. CỮ ĂN / DINH DƯỠNG (FEEDING)
        elif any(w in converted_text for w in ["sữa", "bú", "ml", "cc", "bình", "cháo", "bột", "ăn dặm", "yến mạch"]):
            intent = "feeding"
            
            # Phân loại loại sữa / thức ăn
            feed_type = "Formula"
            if "mẹ" in converted_text:
                feed_type = "Breast"
            elif any(w in converted_text for w in ["cháo", "bột", "ăn dặm", "yến mạch", "nghiền", "bơ", "bí đỏ"]):
                feed_type = "Solids"

            # Tìm lượng sữa / lượng thức ăn (ml / g)
            amount_match = re.search(r"(\d+(?:\.\d+)?)\s*(ml|cc|g|gam|bình)?", converted_text)
            amount_val = None
            if amount_match:
                try:
                    val = float(amount_match.group(1))
                    unit_str = amount_match.group(2) or "ml"
                    if unit_str == "bình" and val == 1.0:
                        amount_val = 150.0 # 1 bình mặc định
                    else:
                        amount_val = val
                except ValueError:
                    pass

            if amount_val is not None:
                # Kiểm tra giới hạn y khoa nhi khoa
                if amount_val > 400.0 and feed_type != "Solids":
                    warnings.append(f"Lượng sữa {amount_val}ml lớn hơn mức bình thường 400ml của 1 cữ bú trẻ nhỏ.")
                elif amount_val < 10.0:
                    warnings.append(f"Lượng sữa {amount_val}ml quá ít, vui lòng xác nhận lại.")

                extracted_data["amount"] = amount_val
                extracted_data["type"] = feed_type
                extracted_data["details"] = f"{int(amount_val)}ml Sữa công thức" if feed_type == "Formula" else (f"{int(amount_val)}ml Sữa mẹ" if feed_type == "Breast" else f"{int(amount_val)}g Ăn dặm")
                canonical_data = {
                    "amount": amount_val,
                    "unit": "g" if feed_type == "Solids" else "ml",
                    "feed_type": feed_type,
                    "details": extracted_data["details"]
                }
            else:
                missing_fields.append("amount")
                suggested_chips = ["60ml", "90ml", "120ml", "150ml", "180ml", "210ml"]
                extracted_data["type"] = feed_type
                extracted_data["amount"] = None
                canonical_data = {"feed_type": feed_type, "amount": None}
                confidence = 0.70

        # C. THAY TÃ BỈM (DIAPER)
        elif any(w in converted_text for w in ["tã", "bỉm", "tè", "ỉa", "ị", "ướt", "đi ngoài", "phân"]):
            intent = "diaper"
            is_dirty = any(w in converted_text for w in ["bẩn", "ỉa", "ị", "phân", "đại tiện", "đi ngoài"])
            diaper_type = "Dirty" if is_dirty else "Wet"
            
            extracted_data["type"] = diaper_type
            canonical_data = {"type": diaper_type}


        # E. THEO DÕI GIẤC NGỦ (SLEEP)
        elif any(w in converted_text for w in ["ngủ", "thức", "dậy", "chợp mắt", "nap"]):
            intent = "sleep"
            action = "start_sleep" if any(w in converted_text for w in ["bắt đầu ngủ", "đi ngủ", "vào giấc"]) else "wake"
            
            extracted_data["action"] = action
            extracted_data["details"] = converted_text
            canonical_data = {"action": action, "details": converted_text}

        else:
            intent = "unknown"
            confidence = 0.20
            warnings.append("Chưa xác định rõ danh mục ghi chép. Vui lòng chọn danh mục tương ứng trên màn hình.")

        # Nếu có cảnh báo phủ định/tương lai, hạ confidence xuống mức an toàn
        if negation_warning:
            confidence = min(confidence, 0.40)

        return VoiceExtractResponse(
            success=(intent != "unknown"),
            intent=intent,
            confidence=round(confidence, 2),
            extracted_data=extracted_data,
            canonical_data=canonical_data,
            missing_fields=missing_fields,
            suggested_chips=suggested_chips,
            warnings=warnings,
            confidence_message="Bóc tách dữ liệu từ giọng nói thành công." if intent != "unknown" else "Vui lòng chọn danh mục ghi chép."
        )

