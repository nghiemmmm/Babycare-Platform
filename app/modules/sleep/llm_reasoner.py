"""
LLM Anomaly Reasoner Module
===========================
Chỉ được kích hoạt khi dự đoán ML rơi vào nhánh BẤT THƯỜNG / ANOMALY:
- Điều tra bối cảnh sức khỏe (Sốt, ốm, mọc răng, tiêm phòng, nợ ngủ).
- Đưa ra độ lệch điều chỉnh quanh Expert Baseline (health_delta_minutes).
- Soạn thảo Lời dặn dò phụ huynh với văn phong Nhi khoa ấm áp, tinh tế.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMAnomalyInvestigationOutput(BaseModel):
    health_delta_minutes: int = Field(
        ...,
        description="Số phút điều chỉnh quanh Expert Baseline do tình trạng sức khỏe (ví dụ -30 đến +10)"
    )
    clinical_rationale: str = Field(
        ...,
        description="Phân tích nguyên nhân lâm sàng ngắn gọn"
    )
    parental_guidance: str = Field(
        ...,
        description="Lời dặn dò ân cần, tinh tế dành riêng cho người mẹ/người chăm sóc"
    )
    red_flag_warning: Optional[str] = Field(
        None,
        description="Dấu hiệu cảnh báo cần thăm khám bác sĩ nếu có"
    )


class LLMPediatricSleepReasoner:
    """
    Chuyên gia Cố vấn Y khoa LLM (Gemini 2.0 / Flash):
    Được đánh thức duy nhất khi ML Prediction bị lệch bất thường.
    """

    SYSTEM_PROMPT = """Bạn là Chuyên gia Nhi khoa và Cố vấn Giấc ngủ Trẻ em của BabyCare AI.
Hệ thống vừa phát hiện dự đoán thời gian thức của em bé có sự bất thường so với chuẩn sinh học thông thường.
Nhiệm vụ của bạn:
1. Đọc bối cảnh sức khỏe gần đây của bé (Nhật ký sốt, tiêm chủng, mọc răng, nợ ngủ hoặc nghi vấn log nhầm giờ).
2. Phân tích nguyên nhân lâm sàng: Bé có đang mệt mỏi, sốt hay trong tuần khủng hoảng không?
3. Đưa ra số phút hiệu chỉnh quanh mốc chuẩn Chuyên gia (health_delta_minutes: thường từ -30p đến +10p).
4. Soạn lời dặn dò phụ huynh với VĂN PHONG NHI KHOA ẤM ÁP, DỊU DÀNG, TINH TẾ. Tuyệt đối không phán xét, không dùng thuật ngữ kỹ thuật thô ráp.

Trả về đúng định dạng JSON."""

    @classmethod
    async def investigate_anomaly(
        cls,
        age_months: float,
        expert_baseline_ww: int,
        abnormal_ml_prediction: float,
        health_logs: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMAnomalyInvestigationOutput:
        health_events = health_logs or []

        user_content = f"""
Thông tin trường hợp bất thường:
- Tuổi của bé: {age_months:.1f} tháng
- Chuẩn Chuyên gia (Expert Baseline): {expert_baseline_ww} phút
- Dự đoán thô từ Machine Learning: {int(abnormal_ml_prediction)} phút (Bị lệch bất thường)
- Nhật ký sức khỏe/biến cố ghi nhận trong 48h qua:
{json.dumps(health_events, ensure_ascii=False, indent=2) if health_events else 'Không có log bệnh lý cụ thể (nghi ngờ do nợ ngủ hoặc phụ huynh ghi nhận nhầm mốc giờ).'}

Hãy phân tích và đưa ra điều chỉnh an toàn quanh mốc Expert Baseline kèm lời khuyên ấm áp cho mẹ.
"""

        # Gọi mô hình LLM qua OpenRouter hoặc Google GenAI
        try:
            from app.AI_agents.providers.openrouter_provider import OpenRouterLLMProvider
            provider = OpenRouterLLMProvider()
            llm = provider.get_chat_model(temperature=0.2)
            structured_llm = llm.with_structured_output(LLMAnomalyInvestigationOutput)

            response = await structured_llm.ainvoke([
                SystemMessage(content=cls.SYSTEM_PROMPT),
                HumanMessage(content=user_content)
            ])
            return response
        except Exception as e:
            logger.info(f"[LLM Reasoner] Áp dụng quy tắc lâm sàng chuẩn khi API bận: {e}")
            # Fallback y khoa chuẩn xác nếu không có kết nối LLM
            delta = -20 if health_events else 0
            reason_text = "Hệ thống ghi nhận dấu hiệu sốt/mệt mỏi từ nhật ký sức khỏe của bé." if health_events else "Hệ thống tự động đưa thời gian thức về mốc an toàn theo tháng tuổi."
            return LLMAnomalyInvestigationOutput(
                health_delta_minutes=delta,
                clinical_rationale=reason_text,
                parental_guidance=(
                    "Mẹ ơi, hôm nay nhịp sinh hoạt của bé có chút xáo trộn so với ngày thường. "
                    "Hệ thống đã đưa thời gian thức về mốc an toàn chuẩn theo lứa tuổi để bé được nghỉ ngơi thoải mái, "
                    "tránh tình trạng bé bị quá mệt nhé."
                )
            )


def expert_ww_ref(age_months: float) -> int:
    if age_months < 2:
        return 60
    if age_months < 5:
        return 100
    if age_months < 9:
        return 140
    if age_months < 14:
        return 200
    return 270
