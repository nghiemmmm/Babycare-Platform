from app.AI_agents.core.reasoner import AIReasoner
from app.AI_agents.orchestrator.state_manager import OverallState
import json

INTENT_PROMPT = """
You are the Intent & Planning Agent for BabyCare AI.
Analyze the user's input and classify their intent into exactly one of these labels:
1. "chat" - General conversation, parenting advice, Q&A.
2. "log_activity" - Recording/logging baby activities (feeding, sleeping, diaper change).
3. "analyze_cry" - Request to diagnose a baby's cry or sound.
4. "check_health" - Logging symptoms, checking fever, or checking medication rules.
5. "check_nutrition" - Checking baby growth logs, nutrition tips, solid foods, or WHO standards.
6. "generate_report" - Request to export or generate health reports (PDF, Word).

Respond with a JSON object containing:
- "intent": The selected label string.
- "confidence": Float between 0.0 and 1.0.

Example JSON output:
{"intent": "log_activity", "confidence": 0.95}

Do not return any other text besides the JSON.
"""

class TaskPlanner:
    def __init__(self):
        self.reasoner = AIReasoner(model_name="gemini-2.5-flash")

    def classify_intent(self, state: OverallState) -> dict:
        """
        Classifies user query intent from messages state.
        """
        messages = state.get("messages", [])
        if not messages:
            return {"extracted_intent": "chat", "next_step": "chat"}

        user_message = messages[-1].content
        try:
            response_text = self.reasoner.reason(prompt=user_message, system_instruction=INTENT_PROMPT)
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
            response_text = await self.reasoner.areason(prompt=user_message, system_instruction=INTENT_PROMPT)
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_text)
            intent = data.get("intent", "chat")
        except Exception:
            intent = "chat"

        return {"extracted_intent": intent, "next_step": intent}
