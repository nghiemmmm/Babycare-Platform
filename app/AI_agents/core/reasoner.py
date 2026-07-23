import os
import time
import json
from datetime import datetime, timezone
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
from app.AI_agents.core.constant import DEFAULT_CHAT_MODEL, DEFAULT_TEMPERATURE

class AIReasoner:
    def __init__(self, model_name: str = DEFAULT_CHAT_MODEL, temperature: float = DEFAULT_TEMPERATURE):
        self.model_name = model_name
        self.model = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature
        )

    def _log_reasoning(self, system_instruction: str, prompt: str, response: str, elapsed: float):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            log_dir = os.path.join(current_dir, "..", "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "ai_reasoning.jsonl")
            
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model_name": self.model_name,
                "elapsed_seconds": elapsed,
                "system_instruction": system_instruction,
                "prompt": prompt,
                "response": response
            }
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            import sys
            print(f"Failed to write AI reasoning log: {str(e)}", file=sys.stderr)

    def reason(self, prompt: str, system_instruction: str = None) -> str:
        """Synchronously reason using the model."""
        messages = []
        if system_instruction:
            messages.append(SystemMessage(content=system_instruction))
        messages.append(HumanMessage(content=prompt))
        
        start_time = time.perf_counter()
        response = self.model.invoke(messages)
        elapsed = time.perf_counter() - start_time
        
        content = response.content
        result = ""
        if isinstance(content, list):
            result = "".join([block.get("text", "") if isinstance(block, dict) else str(block) for block in content])
        else:
            result = str(content)
            
        self._log_reasoning(system_instruction, prompt, result, elapsed)
        return result

    async def areason(self, prompt: str, system_instruction: str = None) -> str:
        """Asynchronously reason using the model."""
        messages = []
        if system_instruction:
            messages.append(SystemMessage(content=system_instruction))
        messages.append(HumanMessage(content=prompt))
        
        start_time = time.perf_counter()
        response = await self.model.ainvoke(messages)
        elapsed = time.perf_counter() - start_time
        
        content = response.content
        result = ""
        if isinstance(content, list):
            result = "".join([block.get("text", "") if isinstance(block, dict) else str(block) for block in content])
        else:
            result = str(content)
            
        self._log_reasoning(system_instruction, prompt, result, elapsed)
        return result
