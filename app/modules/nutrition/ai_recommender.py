"""
Nutrition Recommender Service Module

Sinh gợi ý dinh dưỡng cá nhân hoá cho bé bằng RAG + Gemini, có xét đến dị ứng
và bệnh lý/triệu chứng đang mắc của bé (không chỉ trả lời câu hỏi như chatbot).
"""
import asyncio
import json
import logging
import re
import time
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel

from app.modules.baby.service import BabyService
from app.modules.nutrition.service import SolidFoodService
from app.modules.nutrition.repository import NutritionRecommendationRepository, WeeklyMealPlanRepository
from app.modules.nutrition.schemas import (
    FoodRecommendationItem,
    FoodAvoidanceItem,
    NutritionRecommendationResponse,
    DayPlan,
    WeeklyMealPlanResponse,
)
from app.modules.health_records.service import HealthRecordService
from app.modules.medication.service import MedicationService
from app.modules.growth_tracking.service import GrowthTrackingService
from app.AI_agents.core.reasoner import AIReasoner
from app.AI_agents.knowledge.retriever import MedicalRetriever
from app.infrastructure.database import get_firestore_db
from app.shared.exceptions import AIGenerationError, EntityNotFoundError, MealPlanLockedError

logger = logging.getLogger(__name__)

# Bản ghi bệnh án cũ hơn khoảng thời gian này không còn được coi là "bệnh đang mắc" -
# bệnh nhẹ thường gặp ở bé (ho, sốt nhẹ, tiêu chảy...) thường đã khỏi sau ~2 tuần.
CURRENT_ILLNESS_WINDOW_DAYS = 14

NUTRITION_RECOMMENDATION_SYSTEM_PROMPT = """
Bạn là chuyên gia dinh dưỡng nhi khoa. Dựa trên hồ sơ bé được cung cấp (tuổi, dị ứng,
bệnh lý đang mắc, nhật ký ăn uống, chỉ số tăng trưởng) và tài liệu dinh dưỡng tham chiếu,
hãy đưa ra gợi ý thực đơn cá nhân hoá.

RÀNG BUỘC QUAN TRỌNG:
1. Chỉ trả về DUY NHẤT một đối tượng JSON hợp lệ, không kèm markdown fence, không có văn bản nào khác.
2. JSON phải đúng cấu trúc:
{
  "recommended_foods": [{"food_name": "...", "reason": "..."}],
  "foods_to_avoid": [{"food_name": "...", "reason": "...", "linked_to": "..."}],
  "summary": "..."
}
3. Mọi mục trong "foods_to_avoid" PHẢI gắn với một dị ứng hoặc bệnh lý CÓ THẬT trong dữ liệu
   được cung cấp (điền đúng tên vào "linked_to") - không suy đoán hay bịa ra dị ứng không có trong dữ liệu.
4. Chỉ dựa trên "Tài liệu dinh dưỡng tham chiếu" bên dưới; nếu tài liệu không đủ thông tin,
   hãy nói rõ điều đó trong "summary" và khuyên phụ huynh tham khảo ý kiến chuyên gia dinh dưỡng.
5. "summary" viết bằng tiếng Việt, ấm áp, dễ hiểu, tối đa vài câu.
"""


class _LLMNutritionOutput(BaseModel):
    recommended_foods: list[FoodRecommendationItem]
    foods_to_avoid: list[FoodAvoidanceItem]
    summary: str


def _extract_json(text: str) -> dict:
    """Bóc JSON khỏi phần trả lời của LLM, kể cả khi bị bọc trong ```json ... ``` fence."""
    stripped = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", stripped, re.DOTALL)
    if fence_match:
        stripped = fence_match.group(1).strip()
    return json.loads(stripped)


class NutritionRecommenderService:
    def __init__(
        self,
        baby_service: Optional[BabyService] = None,
        solid_food_service: Optional[SolidFoodService] = None,
        health_service: Optional[HealthRecordService] = None,
        medication_service: Optional[MedicationService] = None,
        growth_service: Optional[GrowthTrackingService] = None,
        retriever: Optional[MedicalRetriever] = None,
        reasoner: Optional[AIReasoner] = None,
    ):
        self.baby_service = baby_service or BabyService()
        self.solid_food_service = solid_food_service or SolidFoodService(self.baby_service)
        self.health_service = health_service or HealthRecordService(self.baby_service)
        self.medication_service = medication_service or MedicationService(self.baby_service)
        self.growth_service = growth_service or GrowthTrackingService(self.baby_service)
        self._retriever = retriever
        self._reasoner = reasoner

    @property
    def retriever(self) -> MedicalRetriever:
        # Lazy init để tránh load FAISS/embedding lúc import module.
        if self._retriever is None:
            self._retriever = MedicalRetriever()
        return self._retriever

    @property
    def reasoner(self) -> AIReasoner:
        # Lazy init: NutritionRecommenderService được khởi tạo dạng singleton module-level
        # trong router.py, nên không được chạm GEMINI_API_KEY lúc import (sẽ crash app khi
        # thiếu key, kể cả với các request không liên quan đến gợi ý dinh dưỡng).
        if self._reasoner is None:
            from app.AI_agents.core.constant import NUTRITION_RECOMMENDER_MODEL
            self._reasoner = AIReasoner(model_name=NUTRITION_RECOMMENDER_MODEL)
        return self._reasoner

    def get_cached(self, baby_id: str, user_id: str) -> Optional[NutritionRecommendationResponse]:
        """Lấy gợi ý đã sinh gần nhất (nếu có). Không gọi LLM."""
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = NutritionRecommendationRepository(baby_id)
        return repo.get("latest")

    def _get_active_conditions(self, baby_id: str, user_id: str) -> list[dict]:
        records = self.health_service.get_history(baby_id, user_id)
        cutoff = datetime.now(timezone.utc) - timedelta(days=CURRENT_ILLNESS_WINDOW_DAYS)
        active = []
        for r in records:
            try:
                recorded_at = datetime.fromisoformat(r.recorded_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue
            if recorded_at >= cutoff:
                active.append({
                    "diagnosis": r.diagnosis,
                    "symptoms": r.symptoms,
                    "recorded_at": r.recorded_at,
                })
        return active

    def _get_averse_ingredients(self, baby_id: str) -> list[dict]:
        """Món từng gây phản ứng xấu (dị ứng/không thích) được ghi trong nhật ký ăn dặm dạng ingredient."""
        db = get_firestore_db()
        docs = db.collection("nutrition_ingredients").where("baby_id", "==", baby_id).stream()
        averse = []
        for doc in docs:
            d = doc.to_dict()
            reaction = (d.get("reaction") or "").lower()
            if "allerg" in reaction or "dislike" in reaction:
                averse.append({"name": d.get("name", ""), "reaction": d.get("reaction", "")})
        return averse

    def _calculate_age_months(self, birth_date_str: str) -> int:
        birth = date.fromisoformat(birth_date_str[:10])
        today = date.today()
        return (today.year - birth.year) * 12 + today.month - birth.month

    def _build_context_prompt(
        self,
        baby,
        age_months: int,
        active_conditions: list[dict],
        recent_foods,
        averse_ingredients: list[dict],
        latest_growth,
        recent_medications,
        rag_context: str,
    ) -> str:
        allergies_text = ", ".join(baby.allergies) if baby.allergies else "Không có"

        if active_conditions:
            conditions_text = "\n".join(
                f"- {c['diagnosis'] or 'Không rõ chẩn đoán'} (triệu chứng: {', '.join(c['symptoms'])}, ghi nhận {c['recorded_at'][:10]})"
                for c in active_conditions
            )
        else:
            conditions_text = "Không có bệnh lý đang diễn ra."

        if recent_foods:
            foods_text = "\n".join(
                f"- {f.food_name}: {f.amount_g or 0}g, phản ứng: {f.reaction or 'chưa ghi nhận'} ({f.logged_at[:10]})"
                for f in recent_foods
            )
        else:
            foods_text = "Chưa có nhật ký ăn dặm."

        if averse_ingredients:
            averse_text = ", ".join(f"{a['name']} ({a['reaction']})" for a in averse_ingredients)
        else:
            averse_text = "Không có"

        growth_text = (
            f"Chiều cao {latest_growth.height}cm, cân nặng {latest_growth.weight}kg (đo ngày {latest_growth.logged_at[:10]})"
            if latest_growth else "Chưa có dữ liệu tăng trưởng"
        )

        if recent_medications:
            medications_text = ", ".join(
                f"{m.medication_name} ({m.dosage})" for m in recent_medications
            )
        else:
            medications_text = "Không có"

        return (
            f"Tên bé: {baby.name}, {age_months} tháng tuổi, giới tính: {baby.gender}\n"
            f"Dị ứng đã biết: {allergies_text}\n"
            f"Bệnh lý đang mắc: \n{conditions_text}\n"
            f"Món từng gây phản ứng xấu: {averse_text}\n"
            f"Nhật ký ăn dặm gần đây:\n{foods_text}\n"
            f"Chỉ số tăng trưởng gần nhất: {growth_text}\n"
            f"Thuốc/vitamin đang dùng gần đây: {medications_text}\n\n"
            f"Tài liệu dinh dưỡng tham chiếu:\n{rag_context}"
        )

    async def generate_recommendation(self, baby_id: str, user_id: str) -> NutritionRecommendationResponse:
        t_start = time.time()
        baby = self.baby_service.get_baby_by_id(baby_id, user_id)
        age_months = self._calculate_age_months(baby.birth_date)

        active_conditions = self._get_active_conditions(baby_id, user_id)
        recent_foods = self.solid_food_service.get_solid_food_history(baby_id, user_id)[:10]
        averse_ingredients = self._get_averse_ingredients(baby_id)
        growth_history = self.growth_service.get_growth_history(baby_id, user_id)
        latest_growth = growth_history[0] if growth_history else None
        recent_medications = self.medication_service.get_medication_history(baby_id, user_id)[:5]
        t_ctx = time.time()
        logger.info(f"[NutritionRecommender Stage 1] Profile & DB context fetched in {(t_ctx - t_start):.3f}s")

        rag_queries: list[tuple[str, Optional[str]]] = [
            (f"Thực đơn ăn dặm phù hợp cho bé {age_months} tháng tuổi", "nutrition_general")
        ]
        if baby.allergies:
            rag_queries.append(
                (f"An toàn thực phẩm cho bé dị ứng {', '.join(baby.allergies)}", "allergy_safety")
            )
        if active_conditions:
            diagnosis_summary = ", ".join(c["diagnosis"] or "" for c in active_conditions if c["diagnosis"])
            if diagnosis_summary:
                rag_queries.append((f"Dinh dưỡng cho bé đang bị {diagnosis_summary}", "illness_diet"))

        try:
            t_rag_start = time.time()
            rag_results = await asyncio.gather(
                *[asyncio.to_thread(self.retriever.retrieve_context, q, 3, domain) for q, domain in rag_queries]
            )
            rag_context = "\n\n".join(
                f"[Nguồn: {domain or 'chung'}]\n{context}"
                for (_, domain), context in zip(rag_queries, rag_results)
            )
            t_rag_end = time.time()
            logger.info(f"[NutritionRecommender Stage 2] Multi-Query RAG ({len(rag_queries)} queries) fetched in {(t_rag_end - t_rag_start):.3f}s")

            context_prompt = self._build_context_prompt(
                baby, age_months, active_conditions, recent_foods, averse_ingredients,
                latest_growth, recent_medications, rag_context
            )

            t_llm_start = time.time()
            raw_response = await self.reasoner.areason(
                prompt=context_prompt,
                system_instruction=NUTRITION_RECOMMENDATION_SYSTEM_PROMPT,
            )
            t_llm_end = time.time()
            logger.info(f"[NutritionRecommender Stage 3] LLM Reasoning finished in {(t_llm_end - t_llm_start):.3f}s (Total pipeline: {(t_llm_end - t_start):.3f}s)")

            parsed = _extract_json(raw_response)
            llm_output = _LLMNutritionOutput.model_validate(parsed)
        except Exception as e:
            logger.error(f"AI nutrition recommendation generation failed for baby {baby_id}: {e}")
            raise AIGenerationError()

        recommendation = NutritionRecommendationResponse(
            baby_id=baby_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            recommended_foods=llm_output.recommended_foods,
            foods_to_avoid=llm_output.foods_to_avoid,
            summary=llm_output.summary,
            based_on_allergies=baby.allergies,
            based_on_conditions=[c["diagnosis"] for c in active_conditions if c["diagnosis"]],
        )

        repo = NutritionRecommendationRepository(baby_id)
        return repo.create(recommendation, doc_id="latest")


WEEKLY_MEAL_PLAN_SYSTEM_PROMPT = """
Bạn là chuyên gia dinh dưỡng nhi khoa. Dựa trên hồ sơ bé được cung cấp và tài liệu dinh dưỡng
tham chiếu, hãy lên thực đơn ăn dặm cho đúng 7 ngày liên tiếp, mỗi ngày 4 bữa: sáng, trưa, tối, phụ.

RÀNG BUỘC QUAN TRỌNG:
1. Chỉ trả về DUY NHẤT một đối tượng JSON hợp lệ, không kèm markdown fence, không có văn bản nào khác.
2. JSON phải đúng cấu trúc:
{
  "days": [
    {"date": "YYYY-MM-DD", "meals": [{"meal_type": "sáng", "food_name": "...", "note": "..."}, ...]}
  ],
  "summary": "..."
}
   "days" phải có đúng 7 phần tử, "date" của từng phần tử PHẢI khớp chính xác và đúng thứ tự với
   danh sách ngày được cung cấp bên dưới - không tự đổi hay bịa ngày khác.
3. Mỗi ngày PHẢI có đúng 4 bữa với "meal_type" lần lượt là "sáng", "trưa", "tối", "phụ".
4. TUYỆT ĐỐI loại trừ mọi món chứa dị ứng hoặc từng gây phản ứng xấu đã biết của bé - không có ngoại lệ.
5. Cố gắng không lặp lại cùng một món quá 2 lần trong cả tuần; nếu tài liệu tham chiếu không đủ đa
   dạng để tránh lặp, được phép lặp nhưng phải nói rõ lý do trong "summary" thay vì bịa món ngoài tài liệu.
6. Chỉ dựa trên "Tài liệu dinh dưỡng tham chiếu" bên dưới; nếu tài liệu không đủ thông tin cho đúng
   độ tuổi của bé, hãy nói rõ điều đó trong "summary" và khuyên phụ huynh tham khảo chuyên gia dinh dưỡng.
7. Nếu có "Phản hồi của phụ huynh" được cung cấp, PHẢI điều chỉnh thực đơn theo đúng phản hồi đó
   (ví dụ tránh hẳn món phụ huynh nói bé không thích hoặc không muốn cho ăn).
8. "summary" viết bằng tiếng Việt, ấm áp, dễ hiểu, tối đa vài câu.
"""


class _LLMWeeklyMealPlanOutput(BaseModel):
    days: list[DayPlan]
    summary: str


class WeeklyMealPlanService(NutritionRecommenderService):
    """Sinh thực đơn ăn dặm 7 ngày - kế thừa NutritionRecommenderService để tái dùng nguyên vẹn
    logic gom dữ liệu bé (allergies, bệnh lý, nhật ký ăn, tăng trưởng...) và các lazy property
    retriever/reasoner, chỉ khác ở prompt/schema đầu ra và cơ chế trạng thái pending/accepted."""

    def get_cached_weekly_plan(self, baby_id: str, user_id: str) -> Optional[WeeklyMealPlanResponse]:
        """Lấy thực đơn tuần đã sinh gần nhất (nếu có). Không gọi LLM."""
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = WeeklyMealPlanRepository(baby_id)
        return repo.get("latest")

    def _check_not_locked(self, existing: Optional[WeeklyMealPlanResponse]) -> None:
        """Chặn tạo mới nếu thực đơn hiện tại đã được chấp nhận và chưa qua hết end_date -
        phải dùng hết trọn 7 ngày của thực đơn đã chấp nhận rồi mới được tạo thực đơn tiếp theo."""
        if existing is None or existing.status != "accepted":
            return
        end = date.fromisoformat(existing.end_date)
        today = date.today()
        if today <= end:
            days_left = (end - today).days
            raise MealPlanLockedError(
                f"Thực đơn tuần hiện tại còn hiệu lực đến {existing.end_date}, "
                f"vui lòng thử lại sau {days_left} ngày."
            )

    async def generate_weekly_plan(
        self, baby_id: str, user_id: str, feedback: Optional[str] = None
    ) -> WeeklyMealPlanResponse:
        repo = WeeklyMealPlanRepository(baby_id)
        existing = repo.get("latest")
        self._check_not_locked(existing)

        baby = self.baby_service.get_baby_by_id(baby_id, user_id)
        age_months = self._calculate_age_months(baby.birth_date)

        active_conditions = self._get_active_conditions(baby_id, user_id)
        recent_foods = self.solid_food_service.get_solid_food_history(baby_id, user_id)[:10]
        averse_ingredients = self._get_averse_ingredients(baby_id)
        growth_history = self.growth_service.get_growth_history(baby_id, user_id)
        latest_growth = growth_history[0] if growth_history else None
        recent_medications = self.medication_service.get_medication_history(baby_id, user_id)[:5]

        start_date = date.today()
        end_date = start_date + timedelta(days=6)
        plan_dates = [start_date + timedelta(days=i) for i in range(7)]

        # Nhiều query RAG theo nhóm thực phẩm khác nhau (thay vì 1 query chung như tính năng
        # gợi ý ngắn) để lấy đủ chunk đa dạng cho 28 món - corpus nutrition_general hiện chỉ có
        # 1 tài liệu, 1 query k=3 không đủ đa dạng để tránh lặp món suốt 7 ngày.
        rag_queries: list[tuple[str, Optional[str]]] = [
            (f"Thực phẩm giàu đạm cho bé {age_months} tháng tuổi ăn dặm", "nutrition_general"),
            (f"Rau củ phù hợp ăn dặm cho bé {age_months} tháng tuổi", "nutrition_general"),
            (f"Trái cây và tinh bột cho bé {age_months} tháng tuổi ăn dặm", "nutrition_general"),
            ("Thực phẩm cần tránh khi bé mới ăn dặm", "nutrition_general"),
        ]
        if baby.allergies:
            rag_queries.append(
                (f"An toàn thực phẩm cho bé dị ứng {', '.join(baby.allergies)}", "allergy_safety")
            )
        if active_conditions:
            diagnosis_summary = ", ".join(c["diagnosis"] or "" for c in active_conditions if c["diagnosis"])
            if diagnosis_summary:
                rag_queries.append((f"Dinh dưỡng cho bé đang bị {diagnosis_summary}", "illness_diet"))

        try:
            rag_results = await asyncio.gather(
                *[asyncio.to_thread(self.retriever.retrieve_context, q, 4, domain) for q, domain in rag_queries]
            )
            rag_context = "\n\n".join(
                f"[Nguồn: {domain or 'chung'}]\n{context}"
                for (_, domain), context in zip(rag_queries, rag_results)
            )

            context_prompt = self._build_context_prompt(
                baby, age_months, active_conditions, recent_foods, averse_ingredients,
                latest_growth, recent_medications, rag_context
            )
            context_prompt += "\n\nDanh sách 7 ngày cần lên thực đơn (theo đúng thứ tự): " + ", ".join(
                d.isoformat() for d in plan_dates
            )
            if feedback:
                context_prompt += f"\n\nPhản hồi của phụ huynh (bắt buộc điều chỉnh theo): {feedback}"

            raw_response = await self.reasoner.areason(
                prompt=context_prompt,
                system_instruction=WEEKLY_MEAL_PLAN_SYSTEM_PROMPT,
            )
            parsed = _extract_json(raw_response)
            llm_output = _LLMWeeklyMealPlanOutput.model_validate(parsed)
        except Exception as e:
            logger.error(f"AI weekly meal plan generation failed for baby {baby_id}: {e}")
            raise AIGenerationError("Không thể tạo thực đơn 7 ngày lúc này, vui lòng thử lại sau.")

        plan = WeeklyMealPlanResponse(
            baby_id=baby_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            status="pending",
            accepted_at=None,
            days=llm_output.days,
            summary=llm_output.summary,
            based_on_allergies=baby.allergies,
            based_on_conditions=[c["diagnosis"] for c in active_conditions if c["diagnosis"]],
        )
        return repo.create(plan, doc_id="latest")

    def accept_weekly_plan(self, baby_id: str, user_id: str) -> WeeklyMealPlanResponse:
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = WeeklyMealPlanRepository(baby_id)
        plan = repo.get("latest")
        if plan is None:
            raise EntityNotFoundError("Chưa có thực đơn nào để chấp nhận")
        if plan.status == "accepted":
            return plan
        return repo.update("latest", {
            "status": "accepted",
            "accepted_at": datetime.now(timezone.utc).isoformat(),
        })
