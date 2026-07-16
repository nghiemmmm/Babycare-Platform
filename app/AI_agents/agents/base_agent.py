from app.AI_agents.core.reasoner import AIReasoner
from typing import Optional

class BaseAgent:
    def __init__(self, name: str, system_instruction: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.name = name
        self.reasoner = AIReasoner(model_name=model_name)
        self.system_instruction = system_instruction

    async def run(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        instruction = system_instruction or self.system_instruction
        return await self.reasoner.areason(prompt=prompt, system_instruction=instruction)
