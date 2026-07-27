from langgraph.graph import StateGraph, START, END
from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.core.reasoner import AIReasoner
from app.AI_agents.tools.implementation.nutrition_tools import NutritionTrackingTool
from app.AI_agents.tools.implementation.health_tools import HealthRecordsTool
from app.AI_agents.tools.implementation.growth_tools import GrowthTrackingTool
from langchain_core.messages import AIMessage, HumanMessage
from datetime import datetime, timezone
import json
from app.AI_agents.utils.prompts import load_prompt
from app.AI_agents.utils.schemas import FeedingLogSchema, MedicationLogSchema, SymptomLogSchema, GrowthLogSchema
from pydantic import ValidationError

class VoiceLoggingGraph:
    def __init__(self):
        self.reasoner = AIReasoner()
        self.nutrition_tool = NutritionTrackingTool()
        self.health_tool = HealthRecordsTool()
        self.growth_tool = GrowthTrackingTool()
        self.extraction_prompt = load_prompt("extraction.txt")

    async def extract_entities_node(self, state: OverallState) -> dict:
        user_message = state["messages"][-1].content
        try:
            response_text = await self.reasoner.areason(prompt=user_message, system_instruction=self.extraction_prompt)
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
            return {"messages": [AIMessage(content="Error: baby_id or user_id is missing in current state.", response_metadata={"created_at": datetime.now(timezone.utc).isoformat()})]}

        try:
            if activity_type == "feeding":
                # Validate using Pydantic
                validated = FeedingLogSchema(**data)
                validated_data = validated.model_dump(exclude_none=True)
                if "logged_at" not in validated_data:
                    validated_data["logged_at"] = datetime.now(timezone.utc).isoformat()
                self.nutrition_tool._run(action="add", baby_id=baby_id, user_id=user_id, data=validated_data)
                msg = f"Đã ghi nhận cữ ăn dặm của bé: {validated_data.get('food_name')} với lượng {validated_data.get('amount_g')}g thành công."
            elif activity_type == "medication":
                # Validate using Pydantic
                validated = MedicationLogSchema(**data)
                validated_data = validated.model_dump(exclude_none=True)
                if "logged_at" not in validated_data:
                    validated_data["logged_at"] = datetime.now(timezone.utc).isoformat()
                self.health_tool._run(action="add_medication", baby_id=baby_id, user_id=user_id, data=validated_data)
                msg = f"Đã ghi nhận cữ dùng thuốc: {validated_data.get('medication_name')} với liều lượng {validated_data.get('dosage')} thành công."
            elif activity_type == "symptom":
                # Validate using Pydantic
                validated = SymptomLogSchema(**data)
                validated_data = validated.model_dump(exclude_none=True)
                self.health_tool._run(action="add_record", baby_id=baby_id, user_id=user_id, data=validated_data)
                msg = f"Đã ghi nhận triệu chứng sức khỏe: {', '.join(validated_data.get('symptoms', []))} thành công."
            elif activity_type == "growth":
                # Validate using Pydantic
                validated = GrowthLogSchema(**data)
                validated_data = validated.model_dump(exclude_none=True)
                self.growth_tool._run(action="add", baby_id=baby_id, user_id=user_id, data=validated_data)
                msg = f"Đã ghi nhận chỉ số đo chiều cao {validated_data.get('height')}cm và cân nặng {validated_data.get('weight')}kg thành công."
            else:
                msg = "Không xác định được dữ liệu nhật ký phù hợp."
        except ValidationError as ve:
            errors_str = "; ".join([f"{e['loc'][0]}: {e['msg']}" for e in ve.errors()])
            msg = f"Lỗi xác thực dữ liệu trích xuất từ AI: {errors_str}."
        except Exception as e:
            msg = f"Lỗi lưu trữ nhật ký: {str(e)}"

        return {"messages": [AIMessage(content=msg, response_metadata={"created_at": datetime.now(timezone.utc).isoformat()})]}

    def compile(self, checkpointer=None):
        """Compile the activity logging subgraph flow.
        
        Pipeline: START → extract_entities → write_to_db → END
        (Speech-to-Text transcription is handled on Frontend)
        """
        builder = StateGraph(OverallState)
        builder.add_node("extract_entities", self.extract_entities_node)
        builder.add_node("write_to_db", self.write_to_db_node)
        
        builder.add_edge(START, "extract_entities")
        builder.add_edge("extract_entities", "write_to_db")
        builder.add_edge("write_to_db", END)
        
        return builder.compile(checkpointer=checkpointer)


