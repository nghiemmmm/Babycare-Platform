"""
Action Parser Engine Module
===========================
Parses raw Vietnamese voice transcripts into a structured List[BabyCareAction] across 4 Core Domains:
1. Feeding (Breast / Formula / Solids)
2. Sleep (Start Sleep / Wake / Nap)
3. Diaper (Wet / Dirty / Both)
4. Medication (Medicine / Vitamin with Safety Confirmation)

Features:
- Fast Deterministic Multi-Action Extraction (< 15ms)
- Negation & Future Temporal Filtering
- Missing Fields & Quick Chips Generator
- Strict Idempotency Key Generation
"""
import re
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.AI_agents.actions.schemas import (
    ActionType,
    ActionStatus,
    ActionRiskLevel,
    BabyCareAction
)
from app.AI_agents.core.fast_voice_parser import FastVoiceParser, STT_ALIASES

logger = logging.getLogger(__name__)


class ActionParserEngine:
    """
    Động cơ bóc tách Action đa hành động Hybrid:
    1. Tầng 1: Fast Deterministic Pure Python Parser (< 5ms) cho các mẫu phổ biến.
    2. Tầng 2: LLM Semantic Parser (Gemini) tự động hiểu ngữ nghĩa tiếng Việt tự nhiên, từ lóng, món ăn lạ.
    """

    @classmethod
    def _generate_idempotency_key(cls, baby_id: str, action_type: str, params: Dict[str, Any]) -> str:
        """Tạo khóa chống trùng lặp dựa trên nội dung hành động."""
        param_str = "_".join(f"{k}:{v}" for k, v in sorted(params.items()))
        raw = f"{baby_id}_{action_type}_{param_str}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    @classmethod
    def _parse_with_llm(cls, text: str, baby_id: str) -> List[BabyCareAction]:
        """
        Sử dụng Gemini LLM để hiểu ngữ nghĩa tiếng Việt tự nhiên và trích xuất Action
        khi bộ lọc nhanh không nhận diện được (LLM Semantic Fallback).
        """
        try:
            from app.AI_agents.models.llm_factory import LLMFactory
            from langchain_core.messages import HumanMessage
            import json

            llm = LLMFactory.get_model()
            prompt = f"""Bạn là AI phân tích nhật ký chăm sóc trẻ sơ sinh & trẻ nhỏ (BabyCare AI).
Nhiệm vụ: Trích xuất câu nói tự nhiên của phụ huynh thành danh sách JSON các hành động chăm sóc bé.

Các loại hành động hỗ trợ (ActionType):
1. CREATE_FEEDING: Cữ bú hoặc ăn dặm.
   - feed_type: "Breast" (sữa mẹ, ti mẹ) | "Formula" (sữa công thức, sữa bột) | "Solids" (ăn dặm, ăn cháo, bột, hoa quả, củ quả, cơm,...)
   - food_name: Tên món ăn hoặc loại sữa (ví dụ: "Bí đỏ nghiền", "Cháo thịt băm", "Sữa mẹ", "Aptamil")
   - amount: Số lượng (ml hoặc gam). Nếu là ăn dặm mà không nói số gam thì để 50.0. Nếu là bú mà không nói ml thì để null.
   - unit: "ml" (cho sữa) hoặc "g" (cho ăn dặm).
2. CREATE_SLEEP: Giấc ngủ của bé.
   - action: "start_sleep" (bắt đầu ngủ, đi ngủ) hoặc "wake" (thức dậy, đã ngủ xong).
   - duration_minutes: Số phút ngủ nếu có (ví dụ ngủ 1 tiếng -> 60).
3. CREATE_DIAPER: Thay tã bỉm.
   - diaper_type: "Wet" (tè ướt) | "Dirty" (đi ngoài, bẩn, ị) | "Both" (cả hai).
4. CREATE_MEDICATION: Uống thuốc, vitamin.
   - medication_name: Tên thuốc hoặc vitamin (ví dụ "Hapacol 150mg", "Vitamin D3").
   - dosage: Liều lượng (ví dụ "1 gói", "150mg", "2 giọt", "5ml").

Nếu câu nói KHÔNG chứa hành động chăm sóc nào hoặc là câu phủ định ("bé không chịu ăn"), trả về mảng rỗng [].

Chỉ trả về JSON thuần túy dạng mảng các object theo cấu trúc:
[
  {{
    "action_type": "CREATE_FEEDING",
    "parameters": {{ "feed_type": "Solids", "food_name": "Bí đỏ nghiền", "amount": 50.0, "unit": "g" }},
    "missing_fields": [],
    "suggested_chips": [],
    "clarification_prompt": null
  }}
]

Câu nói của phụ huynh: "{text}"
JSON:"""

            resp = llm.invoke([HumanMessage(content=prompt)])
            raw_content = resp.content.strip()
            
            # Xóa markdown code block nếu có
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:]
            if raw_content.startswith("```"):
                raw_content = raw_content[3:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]
            raw_content = raw_content.strip()

            data = json.loads(raw_content)
            if not isinstance(data, list):
                return []

            actions: List[BabyCareAction] = []
            for item in data:
                a_type_str = item.get("action_type")
                try:
                    a_type = ActionType(a_type_str)
                except Exception:
                    continue

                params = item.get("parameters", {})
                missing = item.get("missing_fields", [])
                chips = item.get("suggested_chips", [])
                prompt_text = item.get("clarification_prompt")
                status = ActionStatus.NEEDS_CLARIFICATION if missing else ActionStatus.READY_TO_EXECUTE
                risk_level = ActionRiskLevel.HIGH if a_type == ActionType.CREATE_MEDICATION else ActionRiskLevel.LOW

                actions.append(BabyCareAction(
                    action_id=f"act_llm_{uuid.uuid4().hex[:8]}",
                    action_type=a_type,
                    baby_id=baby_id,
                    parameters=params,
                    risk_level=risk_level,
                    status=status,
                    requires_confirmation=(risk_level == ActionRiskLevel.HIGH),
                    idempotency_key=cls._generate_idempotency_key(baby_id, a_type.value, params),
                    missing_fields=missing,
                    suggested_chips=chips,
                    clarification_prompt=prompt_text
                ))
            return actions
        except Exception as e:
            logger.warning(f"[ActionParser] LLM Semantic Fallback gặp lỗi: {e}")
            return []

    @classmethod
    def _parse_deterministic(cls, text: str, baby_id: str) -> List[BabyCareAction]:
        """
        Bộ bóc tách nhanh siêu tốc bằng quy tắc thuần Python (< 5ms).
        """
        norm_text = FastVoiceParser.normalize_text(text)
        converted_text = FastVoiceParser.convert_vietnamese_words_to_number(norm_text)

        # Kiểm tra câu phủ định hoặc mốc tương lai
        negation_warning = FastVoiceParser.detect_negation_or_future(norm_text)
        if negation_warning:
            logger.info(f"[ActionParser] Chặn sinh Action do phát hiện phủ định/tương lai: {negation_warning}")
            return []

        actions: List[BabyCareAction] = []

        # ── 1. DOMAIN: UỐNG THUỐC (MEDICATION) ─────────────────────────────────
        if any(w in converted_text for w in ["thuốc", "hapacol", "paracetamol", "vitamin", "siro", "kháng sinh"]):
            med_name = "Hapacol 150mg"
            if "paracetamol" in converted_text:
                med_name = "Paracetamol"
            elif "vitamin" in converted_text:
                med_name = "Vitamin D3 K2"
            elif "hapacol" in converted_text:
                med_name = "Hapacol 150mg"
            elif "siro" in converted_text:
                med_name = "Siro ho Nhi khoa"

            mg_match = re.search(r"(\d+(?:\.\d+)?)\s*mg", converted_text)
            dose_match = re.search(r"(\d+(?:\.\d+)?)\s*(giọt|viên|gói|ml)", converted_text)
            dosage_val = None
            if mg_match:
                dosage_val = f"{mg_match.group(1)}mg"
            elif dose_match:
                dosage_val = f"{dose_match.group(1)}{dose_match.group(2)}"

            params = {"medication_name": med_name, "dosage": dosage_val}
            missing_fields = []
            suggested_chips = []
            clarification_prompt = None
            status = ActionStatus.READY_TO_EXECUTE

            if not dosage_val:
                missing_fields.append("dosage")
                suggested_chips = ["80mg", "150mg", "250mg", "1 gói", "1/2 gói", "5ml"]
                clarification_prompt = f"Bé uống {med_name} với liều lượng bao nhiêu ạ?"
                status = ActionStatus.NEEDS_CLARIFICATION

            actions.append(BabyCareAction(
                action_id=f"act_med_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.CREATE_MEDICATION,
                baby_id=baby_id,
                parameters=params,
                risk_level=ActionRiskLevel.HIGH,
                status=status,
                requires_confirmation=True,
                idempotency_key=cls._generate_idempotency_key(baby_id, ActionType.CREATE_MEDICATION.value, params),
                missing_fields=missing_fields,
                suggested_chips=suggested_chips,
                clarification_prompt=clarification_prompt
            ))

        # ── 2. DOMAIN: CỮ BÚ & ĂN DẶM (FEEDING & SOLIDS) ─────────────────────
        feeding_triggers = [
            "sữa", "bú", "cháo", "bột", "ăn dặm", "ăn", "yến mạch", "bình sữa",
            "bí đỏ", "bí đó", "khoai", "cà rốt", "bơ", "chuối", "nghiền", "trái cây", "súp"
        ]
        if any(w in converted_text for w in feeding_triggers):
            if "mẹ" in converted_text:
                feed_type = "Breast"
                food_name = "Sữa mẹ"
            elif any(w in converted_text for w in ["cháo", "bột", "ăn dặm", "yến mạch", "nghiền", "bơ", "bí đỏ", "bí đó", "khoai", "cà rốt", "chuối", "ăn", "súp"]):
                feed_type = "Solids"
                if "bí đỏ" in converted_text or "bí đó" in converted_text:
                    food_name = "Bí đỏ nghiền"
                elif "khoai" in converted_text:
                    food_name = "Khoai lang nghiền"
                elif "bơ" in converted_text:
                    food_name = "Bơ nghiền"
                elif "cà rốt" in converted_text:
                    food_name = "Cà rốt nghiền"
                elif "chuối" in converted_text:
                    food_name = "Chuối nghiền"
                elif "cháo" in converted_text:
                    food_name = "Cháo dinh dưỡng"
                elif "bột" in converted_text:
                    food_name = "Bột ăn dặm"
                elif "yến mạch" in converted_text:
                    food_name = "Yến mạch"
                else:
                    m_food = re.search(r"ăn\s+([a-zà-ỹ\s]+)", converted_text)
                    if m_food:
                        food_name = f"{m_food.group(1).strip().capitalize()} (Ăn dặm)"
                    else:
                        food_name = "Ăn dặm dinh dưỡng"
            else:
                feed_type = "Formula"
                food_name = "Sữa công thức"

            amount_match = re.search(r"(\d+(?:\.\d+)?)\s*(ml|cc|g|gam|bình|bát|chén|hũ)?", converted_text)
            amount_val = None
            if amount_match:
                try:
                    val = float(amount_match.group(1))
                    unit_str = amount_match.group(2) or ("g" if feed_type == "Solids" else "ml")
                    if unit_str == "bình" and val == 1.0:
                        amount_val = 150.0
                    elif unit_str in ["bát", "chén", "hũ"] and val == 1.0:
                        amount_val = 100.0
                    else:
                        amount_val = val
                except ValueError:
                    pass
            elif "nửa bát" in converted_text or "nửa chén" in converted_text:
                amount_val = 50.0
            elif "1 bát" in converted_text or "1 chén" in converted_text:
                amount_val = 100.0
            elif feed_type == "Solids":
                amount_val = 50.0

            params = {
                "amount": amount_val,
                "unit": "g" if feed_type == "Solids" else "ml",
                "feed_type": feed_type,
                "food_name": food_name
            }
            missing_fields = []
            suggested_chips = []
            clarification_prompt = None
            status = ActionStatus.READY_TO_EXECUTE

            if amount_val is None:
                missing_fields.append("amount")
                if feed_type == "Solids":
                    suggested_chips = ["30g", "50g", "80g", "100g", "1/2 chén", "1 chén"]
                    clarification_prompt = f"Bé đã ăn bao nhiêu {food_name} vậy mẹ?"
                else:
                    suggested_chips = ["60ml", "90ml", "120ml", "150ml", "180ml", "210ml"]
                    clarification_prompt = f"Bé bú bao nhiêu ml {food_name} vậy mẹ?"
                status = ActionStatus.NEEDS_CLARIFICATION

            actions.append(BabyCareAction(
                action_id=f"act_feed_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.CREATE_FEEDING,
                baby_id=baby_id,
                parameters=params,
                risk_level=ActionRiskLevel.LOW,
                status=status,
                requires_confirmation=False,
                idempotency_key=cls._generate_idempotency_key(baby_id, ActionType.CREATE_FEEDING.value, params),
                missing_fields=missing_fields,
                suggested_chips=suggested_chips,
                clarification_prompt=clarification_prompt
            ))

        # ── 3. DOMAIN: THEO DÕI GIẤC NGỦ (SLEEP) ──────────────────────────────
        clean_sleep_text = converted_text.replace("công thức", "")
        if any(w in clean_sleep_text for w in ["ngủ", "thức dậy", "thức giấc", "dậy", "chợp mắt", "nap", "vào giấc", "thức"]):
            action_name = "start_sleep" if any(w in clean_sleep_text for w in ["bắt đầu ngủ", "đi ngủ", "vào giấc", "rồi ngủ"]) else "wake"
            
            dur_match = re.search(r"(\d+(?:\.\d+)?)\s*(tiếng|giờ|phút)", clean_sleep_text)

            duration_minutes = None
            if dur_match:
                val = float(dur_match.group(1))
                unit = dur_match.group(2)
                if unit in ["tiếng", "giờ"]:
                    duration_minutes = int(val * 60)
                else:
                    duration_minutes = int(val)

            params = {"action": action_name, "duration_minutes": duration_minutes}
            actions.append(BabyCareAction(
                action_id=f"act_sleep_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.CREATE_SLEEP,
                baby_id=baby_id,
                parameters=params,
                risk_level=ActionRiskLevel.LOW,
                status=ActionStatus.READY_TO_EXECUTE,
                requires_confirmation=False,
                idempotency_key=cls._generate_idempotency_key(baby_id, ActionType.CREATE_SLEEP.value, params)
            ))

        # ── 4. DOMAIN: THAY TÃ BỈM (DIAPER) ───────────────────────────────────
        if any(w in converted_text for w in ["tã", "bỉm", "tè", "ỉa", "ị", "ướt", "đi ngoài", "phân"]):
            is_dirty = any(w in converted_text for w in ["bẩn", "ỉa", "ị", "phân", "đại tiện", "đi ngoài"])
            is_wet = any(w in converted_text for w in ["tè", "ướt", "dầm"])
            
            if is_dirty and is_wet:
                diaper_type = "Both"
            elif is_dirty:
                diaper_type = "Dirty"
            else:
                diaper_type = "Wet"

            params = {"diaper_type": diaper_type}
            actions.append(BabyCareAction(
                action_id=f"act_diaper_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.CREATE_DIAPER,
                baby_id=baby_id,
                parameters=params,
                risk_level=ActionRiskLevel.LOW,
                status=ActionStatus.READY_TO_EXECUTE,
                requires_confirmation=False,
                idempotency_key=cls._generate_idempotency_key(baby_id, ActionType.CREATE_DIAPER.value, params)
            ))

        return actions

    @classmethod
    def parse_actions(cls, text: str, baby_id: str) -> List[BabyCareAction]:
        """
        Entry point: Phân tích câu thoại bằng kiến trúc Hybrid 2 tầng:
        - Tầng 1: Fast Deterministic Parser (< 5ms)
        - Tầng 2: Gemini LLM Semantic Parser (Fallback thông minh cho mọi câu nói tự nhiên)
        """
        if not text or not text.strip():
            return []

        # 1. Thử Fast Parser trước
        actions = cls._parse_deterministic(text=text, baby_id=baby_id)
        if actions:
            return actions

        # 2. Nếu Fast Parser không trích xuất được -> Chuyển sang LLM Semantic Parser
        return cls._parse_with_llm(text=text, baby_id=baby_id)

