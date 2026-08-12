from langgraph.graph import StateGraph, START, END
from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.core.reasoner import AIReasoner
from app.ai.cry_classifier import CryClassifier
from app.modules.nutrition.service import SolidFoodService
from langchain_core.messages import AIMessage
import json
from app.AI_agents.core.constant import CRY_REASONER_PROMPT

class CryAnalysisGraph:
    def __init__(self):
        from app.AI_agents.core.constant import CRY_ANALYSIS_MODEL
        self.classifier = CryClassifier()
        self.reasoner = AIReasoner(model_name=CRY_ANALYSIS_MODEL)
        self.nutrition_service = SolidFoodService()

    async def detect_cry_node(self, state: OverallState) -> dict:
        data = state.get("extracted_data") or {}
        filename = data.get("audio_file", "unknown_cry_tired.wav")
        prediction, confidence, reason_scores = self.classifier.predict(filename)
        soothing_sound = self.classifier.get_soothing_sound(prediction)
        
        updated_data = state.get("extracted_data", {}).copy()
        updated_data.update({
            "cry_prediction": prediction,
            "cry_confidence": confidence,
            "reason_scores": reason_scores,
            "soothing_sound": soothing_sound
        })
        return {"extracted_data": updated_data}

    async def context_aggregator_node(self, state: OverallState) -> dict:
        baby_id = state.get("baby_id")
        user_id = state.get("current_user_id")
        
        history_str = "chưa có dữ liệu sinh hoạt gần đây."
        if baby_id and user_id:
            try:
                logs = self.nutrition_service.get_solid_food_history(baby_id, user_id)
                if logs:
                    latest = logs[0]
                    history_str = f"Ăn dặm gần nhất: {latest.food_name} lượng {latest.amount_g}g vào lúc {latest.logged_at}"
            except Exception:
                pass
                
        updated_data = state.get("extracted_data", {}).copy()
        updated_data["feeding_history"] = history_str
        return {"extracted_data": updated_data}

    async def reason_cry_node(self, state: OverallState) -> dict:
        data = state.get("extracted_data") or {}
        predicted_reason = data.get("cry_prediction", "unknown")
        confidence = int(data.get("cry_confidence", 0.0) * 100)
        feeding_history = data.get("feeding_history", "chưa có dữ liệu")
        soothing_sound = data.get("soothing_sound", "classic_lullaby")

        instruction = CRY_REASONER_PROMPT.format(
            predicted_reason=predicted_reason,
            confidence=confidence,
            feeding_history=feeding_history
        )

        try:
            advice = await self.reasoner.areason(
                prompt="Hãy đưa ra chẩn đoán và lời khuyên dỗ bé.",
                system_instruction=instruction
            )
        except Exception as e:
            advice = f"Không kết nối được dịch vụ chẩn đoán AI: {str(e)}"

        full_message = f"🤖 [Chẩn đoán tiếng khóc]\n- Lý do dự đoán qua âm thanh: {predicted_reason} ({confidence}%)\n- Âm thanh đề xuất dỗ bé: {soothing_sound}\n\nLời khuyên từ chuyên gia:\n{advice}"
        return {"messages": [AIMessage(content=full_message)]}

    def compile(self, checkpointer=None):
        """Compile the cry analysis subgraph flow."""
        builder = StateGraph(OverallState)
        builder.add_node("detect_cry", self.detect_cry_node)
        builder.add_node("context_aggregator", self.context_aggregator_node)
        builder.add_node("reason_cry", self.reason_cry_node)

        builder.add_edge(START, "detect_cry")
        builder.add_edge("detect_cry", "context_aggregator")
        builder.add_edge("context_aggregator", "reason_cry")
        builder.add_edge("reason_cry", END)

        return builder.compile(checkpointer=checkpointer)
