from app.AI_agents.core.reasoner import AIReasoner
from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.core.constant import INTENT_PROMPT
import json

class TaskPlanner:
    def __init__(self):
        from app.AI_agents.core.constant import TASK_PLANNER_MODEL
        self.reasoner = AIReasoner(model_name=TASK_PLANNER_MODEL)

    def _call_pollinations(self, prompt: str) -> str:
        import urllib.request
        import json
        
        url = "https://text.pollinations.ai/"
        payload = {
            "messages": [
                {"role": "system", "content": INTENT_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "model": "openai",
            "jsonMode": True
        }
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode("utf-8")

    def classify_intent(self, state: OverallState) -> dict:
        """
        Classifies user query intent from messages state.
        """
        messages = state.get("messages", [])
        if not messages:
            return {"extracted_intent": "chat", "next_step": "chat"}

        user_message = messages[-1].content
        try:
            response_text = self._call_pollinations(user_message)
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_text)
            intent = data.get("intent", "chat")
        except Exception:
            intent = "chat"

        return {"extracted_intent": intent, "next_step": intent}

    async def aclassify_intent(self, state: OverallState) -> dict:
        """
        Classifies user query intent asynchronously using Gemini Flash AIReasoner.
        """
        messages = state.get("messages", [])
        if not messages:
            return {"extracted_intent": "chat", "next_step": "chat"}

        user_message = messages[-1].content
        import time, uuid
        from datetime import datetime, timezone
        t0 = time.time()
        intent = "chat"

        msg_lower = user_message.lower()
        # Fast keyword pre-checks for health & nutrition
        if any(k in msg_lower for k in ["sốt", "nhiệt độ", "hapacol", "thuốc", "bệnh", "bác sĩ", "ho", "sổ mũi", "co giật", "triệu chứng"]):
            intent = "check_health"
        elif any(k in msg_lower for k in ["ăn", "sữa", "bú", "cháo", "bột", "dinh dưỡng", "cân nặng", "chiều cao", "whos", "thực đơn"]):
            intent = "check_nutrition"
        else:
            try:
                response_text = await self.reasoner.areason(
                    prompt=user_message,
                    system_instruction=INTENT_PROMPT
                )
                cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
                data = json.loads(cleaned_text)
                intent = data.get("intent", "chat")
            except Exception:
                # Fallback to pollinations or chat
                try:
                    import asyncio
                    res_p = await asyncio.get_event_loop().run_in_executor(None, self._call_pollinations, user_message)
                    data = json.loads(res_p.replace("```json", "").replace("```", "").strip())
                    intent = data.get("intent", "chat")
                except Exception:
                    intent = "chat"

        t1 = time.time()
        step = {
            "id": f"step_{uuid.uuid4().hex[:6]}",
            "tool_name": "TaskPlanner",
            "display_name": "Phân tích ý định câu hỏi (Intent Classifier)",
            "args": {"message": user_message[:40]},
            "status": "completed",
            "result_summary": f"Kết quả bóc tách: '{intent}'",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "duration_ms": int((t1 - t0) * 1000)
        }

        return {"extracted_intent": intent, "next_step": intent, "tool_steps": [step]}
