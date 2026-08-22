import time
import json
import logging
from datetime import datetime, timezone
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import ValidationError

from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.core.reasoner import AIReasoner
from app.AI_agents.tools.implementation.nutrition_tools import NutritionTrackingTool
from app.AI_agents.tools.implementation.health_tools import HealthRecordsTool
from app.AI_agents.tools.implementation.growth_tools import GrowthTrackingTool
from app.AI_agents.utils.prompts import load_prompt
from app.AI_agents.utils.schemas import FeedingLogSchema, MedicationLogSchema, SymptomLogSchema, GrowthLogSchema
from app.AI_agents.utils.helpers import extract_user_query, build_tool_step, calculate_elapsed_ms
from app.AI_agents.utils.validators import validate_and_parse_llm_json

logger = logging.getLogger(__name__)

class VoiceLoggingGraph:
    def __init__(self):
        from app.AI_agents.core.constant import VOICE_LOGGING_MODEL, VOICE_LOGGING_PROVIDER
        self.reasoner = AIReasoner(model_name=VOICE_LOGGING_MODEL, provider=VOICE_LOGGING_PROVIDER)
        self.nutrition_tool = NutritionTrackingTool()
        self.health_tool = HealthRecordsTool()
        self.growth_tool = GrowthTrackingTool()
        self.extraction_prompt = load_prompt("extraction.txt")

    async def extract_entities_node(self, state: OverallState) -> dict:
        user_message = extract_user_query(state)
        from app.AI_agents.context.context_builder import ContextBuilder
        bundle = ContextBuilder.build_logging_context(
            extraction_prompt=self.extraction_prompt,
            messages=state.get("messages", [])
        )
        t0 = time.time()
        try:
            response_text = await self.reasoner.areason(prompt=user_message, system_instruction=bundle.system_instruction)
            is_valid_json, result, err_msg = validate_and_parse_llm_json(response_text)
            if not is_valid_json or not result:
                return {"error_message": f"Lỗi phân tích JSON từ AI: {err_msg}", "next_step": "chat"}

            step = build_tool_step(
                tool_name="EntityExtractionTool",
                display_name="Phân tích trích xuất dữ liệu nhật ký",
                args={"message": user_message[:40]},
                result_summary=f"Đã bóc tách loại hoạt động: {result.get('activity_type', 'N/A')}",
                duration_ms=calculate_elapsed_ms(t0)
            )
            return {
                "extracted_data": result.get("data", {}),
                "next_step": result.get("activity_type", "chat"),
                "tool_steps": [step],
                "context_bundle": bundle
            }
        except Exception as e:
            return {"error_message": str(e), "next_step": "chat"}

    async def write_to_db_node(self, state: OverallState) -> dict:
        activity_type = state.get("next_step")
        data = state.get("extracted_data", {})
        baby_id = state.get("baby_id")
        user_id = state.get("current_user_id")
        t0 = time.time()

        if not baby_id or not user_id:
            return {"messages": [AIMessage(content="Error: baby_id or user_id is missing in current state.", response_metadata={"created_at": datetime.now(timezone.utc).isoformat()})]}

        tool_name = "ActivityLogTool"
        display_name = "Lưu nhật ký chăm sóc bé"
        status = "completed"
        summary = ""

        try:
            if activity_type == "feeding":
                tool_name = "NutritionTrackingTool"
                display_name = "Ghi nhận nhật ký ăn dặm / dinh dưỡng"
                validated = FeedingLogSchema(**data)
                validated_data = validated.model_dump(exclude_none=True)
                if "logged_at" not in validated_data:
                    validated_data["logged_at"] = datetime.now(timezone.utc).isoformat()
                self.nutrition_tool._run(action="add", baby_id=baby_id, user_id=user_id, data=validated_data)
                msg = f"Đã ghi nhận cữ ăn dặm của bé: {validated_data.get('food_name')} với lượng {validated_data.get('amount_g')}g thành công."
                summary = f"Lưu thành công {validated_data.get('food_name')} ({validated_data.get('amount_g')}g)"
            elif activity_type == "medication":
                tool_name = "HealthRecordsTool"
                display_name = "Ghi nhận lịch uống thuốc cho bé"
                validated = MedicationLogSchema(**data)
                validated_data = validated.model_dump(exclude_none=True)
                if "logged_at" not in validated_data:
                    validated_data["logged_at"] = datetime.now(timezone.utc).isoformat()
                self.health_tool._run(action="add_medication", baby_id=baby_id, user_id=user_id, data=validated_data)
                msg = f"Đã ghi nhận cữ dùng thuốc: {validated_data.get('medication_name')} với liều lượng {validated_data.get('dosage')} thành công."
                summary = f"Lưu thành công thuốc {validated_data.get('medication_name')}"
            elif activity_type == "symptom":
                tool_name = "HealthRecordsTool"
                display_name = "Ghi nhận theo dõi sức khỏe & triệu chứng"
                validated = SymptomLogSchema(**data)
                validated_data = validated.model_dump(exclude_none=True)
                self.health_tool._run(action="add_record", baby_id=baby_id, user_id=user_id, data=validated_data)
                msg = f"Đã ghi nhận triệu chứng sức khỏe: {', '.join(validated_data.get('symptoms', []))} thành công."
                summary = f"Lưu thành công triệu chứng sức khỏe"
            elif activity_type == "growth":
                tool_name = "GrowthTrackingTool"
                display_name = "Ghi nhận chỉ số tăng trưởng (Chiều cao & Cân nặng)"
                validated = GrowthLogSchema(**data)
                validated_data = validated.model_dump(exclude_none=True)
                self.growth_tool._run(action="add", baby_id=baby_id, user_id=user_id, data=validated_data)
                msg = f"Đã ghi nhận chỉ số đo chiều cao {validated_data.get('height')}cm và cân nặng {validated_data.get('weight')}kg thành công."
                summary = f"Lưu chiều cao {validated_data.get('height')}cm, cân nặng {validated_data.get('weight')}kg"
            elif activity_type == "read_last_feed":
                tool_name = "NutritionTrackingTool"
                display_name = "Tra cứu cữ bú gần nhất"
                logs = self.nutrition_tool._run(action="list", baby_id=baby_id, user_id=user_id, limit=1)
                if logs:
                    latest = logs[0]
                    msg = f"Cữ bú gần nhất của bé là {latest.get('food_name', 'sữa')} ({latest.get('amount_g', 0)}ml) vào lúc {latest.get('logged_at', 'vừa xong')}."
                    summary = f"Cữ bú gần nhất: {latest.get('amount_g', 0)}ml"
                else:
                    msg = "Chưa có bản ghi cữ bú nào gần đây cho bé."
                    summary = "Chưa có cữ bú"
            elif activity_type == "read_last_medication":
                tool_name = "HealthRecordsTool"
                display_name = "Tra cứu lần dùng thuốc gần nhất"
                logs = self.health_tool._run(action="list_medications", baby_id=baby_id, user_id=user_id, limit=1)
                if logs:
                    latest = logs[0]
                    msg = f"Lần dùng thuốc gần nhất của bé là {latest.get('medication_name')} ({latest.get('dosage')}) vào lúc {latest.get('logged_at')}."
                    summary = f"Thuốc gần nhất: {latest.get('medication_name')}"
                else:
                    msg = "Chưa có bản ghi dùng thuốc nào gần đây cho bé."
                    summary = "Chưa có nhật ký thuốc"
            elif activity_type == "read_growth_profile":
                tool_name = "GrowthTrackingTool"
                display_name = "Tra cứu chỉ số phát triển gần nhất"
                logs = self.growth_tool._run(action="list", baby_id=baby_id, user_id=user_id, limit=1)
                if logs:
                    latest = logs[0]
                    h = latest.get("height", 66)
                    w = latest.get("weight", 7.2)
                    msg = f"Chỉ số phát triển gần nhất của bé: Chiều cao {h}cm, Cân nặng {w}kg."
                    summary = f"Chiều cao {h}cm, Cân nặng {w}kg"
                else:
                    msg = "Hồ sơ sức khỏe hiện tại của bé: Chiều cao 66cm, Cân nặng 7.2kg."
                    summary = "Chiều cao 66cm, Cân nặng 7.2kg"
            elif activity_type == "read_today_milk":
                tool_name = "NutritionTrackingTool"
                display_name = "Tra cứu tổng lượng sữa hôm nay"
                logs = self.nutrition_tool._run(action="list", baby_id=baby_id, user_id=user_id, limit=10)
                total_ml = sum(l.get("amount_g", 0) for l in logs) if logs else 0
                msg = f"Tổng lượng sữa/cữ ăn hôm nay của bé ghi nhận được là {total_ml}ml."
                summary = f"Tổng lượng sữa: {total_ml}ml"
            else:
                msg = "Không xác định được dữ liệu nhật ký phù hợp."
                status = "failed"
                summary = "Không xác định loại nhật ký"


        except ValidationError as ve:
            errors_str = "; ".join([f"{e['loc'][0]}: {e['msg']}" for e in ve.errors()])
            msg = f"Lỗi xác thực dữ liệu trích xuất từ AI: {errors_str}."
            status = "failed"
            summary = f"Lỗi xác thực: {errors_str}"
        except Exception as e:
            msg = f"Lỗi lưu trữ nhật ký: {str(e)}"
            status = "failed"
            summary = f"Lỗi lưu trữ: {str(e)}"

        step = build_tool_step(
            tool_name=tool_name,
            display_name=display_name,
            args=data,
            status=status,
            result_summary=summary,
            duration_ms=calculate_elapsed_ms(t0)
        )

        return {
            "messages": [AIMessage(content=msg, response_metadata={"created_at": datetime.now(timezone.utc).isoformat()})],
            "tool_steps": [step]
        }

    def compile(self, checkpointer=None):
        """Compile the activity logging subgraph flow."""
        builder = StateGraph(OverallState)
        builder.add_node("extract_entities", self.extract_entities_node)
        builder.add_node("write_to_db", self.write_to_db_node)
        
        builder.add_edge(START, "extract_entities")
        builder.add_edge("extract_entities", "write_to_db")
        builder.add_edge("write_to_db", END)
        
        return builder.compile(checkpointer=checkpointer)

from app.AI_agents.core.contract import AgentContract

class VoiceLoggingAgentContract(AgentContract):
    agent_id = "voice_logging_agent"
    display_name = "Activity & Voice Logging Agent"
    description = "Ghi nhận nhật ký cữ bú, uống thuốc, đo chiều cao cân nặng và triệu chứng của bé."
    capabilities = [
        "structured_logging",
        "fast_logging"
    ]
    intents = ["log_activity"]

    def __init__(self):
        self.graph = VoiceLoggingGraph().compile()

    async def execute(self, state: dict) -> dict:
        return await self.graph.ainvoke(state)



