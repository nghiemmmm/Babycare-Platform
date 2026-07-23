from app.AI_agents.core.reasoner import AIReasoner
from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.core.constant import INTENT_PROMPT
import json

class TaskPlanner:
    def __init__(self):
        # Giữ reasoner để tương thích nếu cần, nhưng định tuyến sẽ dùng API miễn phí Pollinations
        self.reasoner = AIReasoner(model_name="gemini-flash-latest")

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
        Classifies user query intent asynchronously from messages state.
        """
        messages = state.get("messages", [])
        if not messages:
            return {"extracted_intent": "chat", "next_step": "chat"}

        user_message = messages[-1].content
        try:
            import asyncio
            response_text = await asyncio.get_event_loop().run_in_executor(
                None, self._call_pollinations, user_message
            )
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_text)
            intent = data.get("intent", "chat")
        except Exception:
            intent = "chat"

        return {"extracted_intent": intent, "next_step": intent}

