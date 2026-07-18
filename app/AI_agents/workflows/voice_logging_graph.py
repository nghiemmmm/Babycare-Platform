from langgraph.graph import StateGraph, START, END
from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.core.reasoner import AIReasoner
from app.AI_agents.tools.implementation.nutrition_tools import NutritionTrackingTool
from app.AI_agents.tools.implementation.health_tools import HealthRecordsTool
from app.AI_agents.tools.implementation.growth_tools import GrowthTrackingTool
from app.ai.speech_to_text import SpeechTranscriber
from app.AI_agents.utils.validators import validate_audio_file
from langchain_core.messages import AIMessage, HumanMessage
from datetime import datetime, timezone
import json

EXTRACTION_PROMPT = """
You are the Entity Extraction Agent for BabyCare AI.
Analyze the user's logged activity request and extract the parameters based on the activity.
Classify the activity into one of: "feeding", "medication", "symptom", "growth".

Extract:
1. For "feeding": food_name, amount_g (float), reaction (optional), notes (optional), logged_at (ISO format or time).
2. For "medication": medication_name, dosage, prescribed_by (optional), notes (optional), logged_at (ISO format or time).
3. For "symptom": symptoms (list of strings), diagnosis (optional), treatment (optional), doctor_name (optional), notes (optional), recorded_at (ISO format or time).
4. For "growth": height (float), weight (float), head_circumference (float, optional).

Respond with a JSON object containing:
- "activity_type": The activity label string.
- "data": The dict containing the extracted properties.

Example JSON output:
{"activity_type": "feeding", "data": {"food_name": "sữa", "amount_g": 120.0, "logged_at": "2026-07-16T08:00:00Z"}}

Do not return any other text besides the JSON.
"""

class VoiceLoggingGraph:
    def __init__(self):
        self.reasoner = AIReasoner(model_name="gemini-flash-latest")
        self.nutrition_tool = NutritionTrackingTool()
        self.health_tool = HealthRecordsTool()
        self.growth_tool = GrowthTrackingTool()
        self.transcriber = SpeechTranscriber()

    async def transcribe_node(self, state: OverallState) -> dict:
        """Convert audio file to text if last message is an audio path."""
        last_message = state["messages"][-1].content
        if validate_audio_file(last_message):
            transcribed = self.transcriber.transcribe(last_message)
            if transcribed:
                # Replace audio path with transcribed text in state
                return {"messages": [HumanMessage(content=transcribed)]}
        return {}

    async def extract_entities_node(self, state: OverallState) -> dict:
        user_message = state["messages"][-1].content
        try:
            response_text = await self.reasoner.areason(prompt=user_message, system_instruction=EXTRACTION_PROMPT)
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            result = json.loads(cleaned_text)
            return {
                "extracted_data": result.get("data", {}),
                "next_step": result.get("activity_type", "chat")
            }
        except Exception as e:
            return {"error_message": str(e), "next_step": "chat"}

    async def write_to_db_node(self, state: OverallState) -> dict:
        activity_type = state.get("next_step")
        data = state.get("extracted_data", {})
        baby_id = state.get("baby_id")
        user_id = state.get("current_user_id")

        if not baby_id or not user_id:
            return {"messages": [AIMessage(content="Error: baby_id or user_id is missing in current state.")]}

        try:
            if activity_type == "feeding":
                if "logged_at" not in data:
                    data["logged_at"] = datetime.now(timezone.utc).isoformat()
                self.nutrition_tool._run(action="add", baby_id=baby_id, user_id=user_id, data=data)
                msg = f"Đã ghi nhận cữ ăn dặm của bé: {data.get('food_name')} với lượng {data.get('amount_g')}g thành công."
            elif activity_type == "medication":
                if "logged_at" not in data:
                    data["logged_at"] = datetime.now(timezone.utc).isoformat()
                self.health_tool._run(action="add_medication", baby_id=baby_id, user_id=user_id, data=data)
                msg = f"Đã ghi nhận cữ dùng thuốc: {data.get('medication_name')} với liều lượng {data.get('dosage')} thành công."
            elif activity_type == "symptom":
                self.health_tool._run(action="add_record", baby_id=baby_id, user_id=user_id, data=data)
                msg = f"Đã ghi nhận triệu chứng sức khỏe: {', '.join(data.get('symptoms', []))} thành công."
            elif activity_type == "growth":
                self.growth_tool._run(action="add", baby_id=baby_id, user_id=user_id, data=data)
                msg = f"Đã ghi nhận chỉ số đo chiều cao {data.get('height')}cm và cân nặng {data.get('weight')}kg thành công."
            else:
                msg = "Không xác định được dữ liệu nhật ký phù hợp."
        except Exception as e:
            msg = f"Lỗi lưu trữ nhật ký: {str(e)}"

        return {"messages": [AIMessage(content=msg)]}

    def compile(self, checkpointer=None):
        """Compile the voice logging subgraph flow.
        
        Pipeline: START → transcribe (STT) → extract_entities → write_to_db → END
        """
        builder = StateGraph(OverallState)
        builder.add_node("transcribe", self.transcribe_node)
        builder.add_node("extract_entities", self.extract_entities_node)
        builder.add_node("write_to_db", self.write_to_db_node)
        
        builder.add_edge(START, "transcribe")
        builder.add_edge("transcribe", "extract_entities")
        builder.add_edge("extract_entities", "write_to_db")
        builder.add_edge("write_to_db", END)
        
        return builder.compile(checkpointer=checkpointer)

