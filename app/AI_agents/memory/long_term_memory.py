import re
import uuid
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional

class FactCategory(str, Enum):
    ALLERGY = "allergy"
    PREFERENCE = "preference"
    MEDICAL_HISTORY = "medical_history"
    SPECIAL_REQUEST = "special_request"
    GENERAL_FACT = "general_fact"

@dataclass
class UserBabyFact:
    id: str
    user_id: str
    baby_id: str
    category: FactCategory
    fact: str
    confidence: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class LongTermMemoryStore:
    """
    Long-Term Memory Store lưu trữ các persistent facts xuyên suốt các thread hội thoại khác nhau.
    Keyed theo (user_id, baby_id).
    """
    _instance: Optional["LongTermMemoryStore"] = None
    _store: Dict[Tuple[str, str], List[UserBabyFact]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LongTermMemoryStore, cls).__new__(cls)
            cls._instance._store = {}
            cls._instance._seed_default_facts()
        return cls._instance

    def _seed_default_facts(self):
        """Dữ liệu mẫu cho Bé Leo & Bé Bo từ AGENTS.md / Database."""
        # Seed cho Bé Leo (Nam, 6 tháng, Dị ứng: Đậu nành)
        self.add_fact(
            user_id="demo_user",
            baby_id="baby_leo",
            category=FactCategory.ALLERGY,
            fact="Bé bị dị ứng nghiêm trọng với Đậu nành (Soy allergy)"
        )

    def add_fact(
        self,
        user_id: str,
        baby_id: str,
        category: FactCategory,
        fact: str,
        confidence: float = 1.0
    ) -> UserBabyFact:
        if not (user_id and baby_id and fact):
            return None

        key = (str(user_id), str(baby_id))
        if key not in self._store:
            self._store[key] = []

        # Deduplicate fact content
        fact_lower = fact.strip().lower()
        for existing in self._store[key]:
            if existing.fact.strip().lower() == fact_lower and existing.category == category:
                return existing

        fact_item = UserBabyFact(
            id=f"fact_{uuid.uuid4().hex[:8]}",
            user_id=str(user_id),
            baby_id=str(baby_id),
            category=category,
            fact=fact.strip(),
            confidence=confidence
        )
        self._store[key].append(fact_item)
        return fact_item

    def get_facts(
        self,
        user_id: str,
        baby_id: str,
        category: Optional[FactCategory] = None
    ) -> List[UserBabyFact]:
        if not (user_id and baby_id):
            return []
        key = (str(user_id), str(baby_id))
        facts = self._store.get(key, [])
        if category:
            return [f for f in facts if f.category == category]
        return list(facts)

    def format_facts_for_context(self, user_id: str, baby_id: str) -> str:
        facts = self.get_facts(user_id, baby_id)
        if not facts:
            return ""

        lines = []
        for f in facts:
            cat_name = f.category.value.upper()
            lines.append(f"- [{cat_name}] {f.fact}")
        return "\n".join(lines)


class FactExtractor:
    """
    Tự động trích xuất các persistent facts (dị ứng, thói quen, tiền sử sức khỏe) từ câu hỏi của người dùng.
    """
    def __init__(self, memory_store: Optional[LongTermMemoryStore] = None):
        self.store = memory_store or LongTermMemoryStore()

    def extract_and_store_facts(
        self,
        user_id: str,
        baby_id: str,
        user_message: str
    ) -> List[UserBabyFact]:
        if not (user_id and baby_id and user_message):
            return []

        extracted_facts: List[UserBabyFact] = []
        msg_lower = user_message.lower()

        # 1. Trích xuất Dị ứng (Allergies)
        allergy_match = re.search(r"(dị ứng|kị|mẫn cảm với)\s+([^\.,!\?]+)", msg_lower)
        if allergy_match:
            allergen = allergy_match.group(2).strip()
            fact_str = f"Bé bị dị ứng / mẫn cảm với {allergen}"
            saved = self.store.add_fact(user_id, baby_id, FactCategory.ALLERGY, fact_str)
            if saved:
                extracted_facts.append(saved)

        # 2. Trích xuất Tiền sử y khoa (Medical History)
        history_match = re.search(r"(tiền sử|từng bị|từng mắc|có bệnh)\s+([^\.,!\?]+)", msg_lower)
        if history_match:
            condition = history_match.group(2).strip()
            fact_str = f"Tiền sử sức khỏe của bé: {condition}"
            saved = self.store.add_fact(user_id, baby_id, FactCategory.MEDICAL_HISTORY, fact_str)
            if saved:
                extracted_facts.append(saved)

        # 3. Trích xuất Thói quen / Sở thích (Preferences)
        pref_match = re.search(r"(thích|ghét|không thích|thói quen)\s+([^\.,!\?]+)", msg_lower)
        if pref_match and not allergy_match and not history_match:
            preference = pref_match.group(0).strip()
            fact_str = f"Thói quen / Sở thích của bé: {preference}"
            saved = self.store.add_fact(user_id, baby_id, FactCategory.PREFERENCE, fact_str)
            if saved:
                extracted_facts.append(saved)

        return extracted_facts
