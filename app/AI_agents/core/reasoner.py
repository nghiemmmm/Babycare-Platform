import os
import time
import json
from datetime import datetime, timezone
from typing import Optional
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage
import logging
from app.core.config import settings
from app.AI_agents.core.constant import DEFAULT_CHAT_MODEL, DEFAULT_TEMPERATURE

logger = logging.getLogger(__name__)

MODEL_PRICING: dict[str, dict[str, float]] = {
    "gemini-3.5-flash-lite": {"input": 0.075, "output": 0.30},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-1.5-flash-latest": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "default": {"input": 0.10, "output": 0.40}
}


class AIReasoner:
    def __init__(self, model_name: str = None, temperature: float = DEFAULT_TEMPERATURE, provider: str = None):
        from app.AI_agents.providers.model_router import ModelRouter

        self.model_name = model_name or settings.OPENROUTER_MODEL or DEFAULT_CHAT_MODEL
        self.provider = provider

        callbacks = []
        if os.getenv("LANGCHAIN_TRACING_V2") == "true":
            try:
                from langchain_core.tracers import LangChainTracer
                tracer = LangChainTracer(
                    project_name=os.getenv("LANGCHAIN_PROJECT", "babycare-ai"),
                    api_key=os.getenv("LANGCHAIN_API_KEY")
                )
                callbacks.append(tracer)
            except Exception as e:
                logger.warning(f"[AIReasoner] Could not attach LangChainTracer: {e}")

        self.model = ModelRouter.get_model(
            model_name=self.model_name,
            provider=self.provider,
            temperature=temperature,
            callbacks=callbacks if callbacks else None
        )

    def _log_reasoning(
        self,
        system_instruction: Optional[str],
        prompt: str,
        response_text: str,
        elapsed: float,
        usage_metadata: Optional[dict] = None
    ):
        """
        Ghi log Financial Observability:
        - prompt_tokens, completion_tokens, total_tokens
        - estimated_cost_usd
        - model_name, provider, elapsed_seconds
        """
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            log_dir = os.path.join(current_dir, "..", "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "ai_reasoning.jsonl")

            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0

            if usage_metadata and isinstance(usage_metadata, dict):
                prompt_tokens = usage_metadata.get("input_tokens") or usage_metadata.get("prompt_tokens") or 0
                completion_tokens = usage_metadata.get("output_tokens") or usage_metadata.get("completion_tokens") or 0
                total_tokens = usage_metadata.get("total_tokens") or (prompt_tokens + completion_tokens)
            
            if not total_tokens:
                # Xấp xỉ số lượng token dựa trên từ vựng nếu không lấy được metadata từ SDK
                prompt_tokens = int(len((prompt or "").split()) * 1.3) + int(len((system_instruction or "").split()) * 1.3)
                completion_tokens = int(len((response_text or "").split()) * 1.3)
                total_tokens = prompt_tokens + completion_tokens

            rates = MODEL_PRICING.get(self.model_name, MODEL_PRICING["default"])
            cost_input = (prompt_tokens / 1_000_000.0) * rates["input"]
            cost_output = (completion_tokens / 1_000_000.0) * rates["output"]
            estimated_cost_usd = round(cost_input + cost_output, 7)

            from app.shared.security import mask_pii_prompt
            from app.shared.context import get_current_trace_id, add_task_cost

            trace_id = get_current_trace_id()
            accumulated_task_cost_usd = add_task_cost(estimated_cost_usd)

            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trace_id": trace_id,
                "model_name": self.model_name,
                "provider": self.provider or "gemini",
                "elapsed_seconds": round(elapsed, 4),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "call_cost_usd": estimated_cost_usd,
                "accumulated_task_cost_usd": accumulated_task_cost_usd,
                "system_instruction": mask_pii_prompt(system_instruction or ""),
                "prompt": mask_pii_prompt(prompt or ""),
                "response": mask_pii_prompt(response_text or "")
            }
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

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
            
        usage = getattr(response, "usage_metadata", None)
        self._log_reasoning(system_instruction, prompt, result, elapsed, usage_metadata=usage)
        return result

    async def areason(self, prompt: str, system_instruction: str = None) -> str:
        """Asynchronously reason using the model for single prompt."""
        messages = []
        if system_instruction:
            messages.append(SystemMessage(content=system_instruction))
        messages.append(HumanMessage(content=prompt))
        
        start_time = time.perf_counter()
        try:
            response = await self.model.ainvoke(messages)
        except Exception as ex:
            ex_str = str(ex).lower()
            if any(k in ex_str for k in ["429", "resource_exhausted", "quota", "rate limit", "exceeded"]):
                logger.warning("[AIReasoner] ⚠️ Model hiện tại dính lỗi 429 Quota. Tự động Fallback sang 'gemini-1.5-flash-latest'...")
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    from app.core.config import settings
                    fallback_model = ChatGoogleGenerativeAI(
                        model="gemini-1.5-flash-latest",
                        google_api_key=settings.GEMINI_API_KEY,
                        temperature=0.2,
                        timeout=15.0
                    )
                    response = await fallback_model.ainvoke(messages)
                except Exception as fallback_ex:
                    logger.error(f"[AIReasoner] Auto-fallback thất bại: {fallback_ex}")
                    raise RuntimeError("⚠️ GEMINI_API_KEY hiện tại đã HẾT QUOTA (Lỗi 429). Vui lòng cập nhật API Key mới vào file .env.")
            else:
                raise ex

        elapsed = time.perf_counter() - start_time
        content = response.content
        result = ""
        if isinstance(content, list):
            result = "".join([block.get("text", "") if isinstance(block, dict) else str(block) for block in content])
        else:
            result = str(content)
            
        usage = getattr(response, "usage_metadata", None)
        self._log_reasoning(system_instruction, prompt, result, elapsed, usage_metadata=usage)
        return result

    async def areason_with_history(self, messages: list[AnyMessage], system_instruction: str = None) -> str:
        """
        Asynchronously reason using the model with multi-turn conversation history.
        `messages` contains previous HumanMessage and AIMessage objects.
        """
        formatted_messages = []
        if system_instruction:
            formatted_messages.append(SystemMessage(content=system_instruction))
        
        formatted_messages.extend(messages)
        
        start_time = time.perf_counter()
        try:
            response = await self.model.ainvoke(formatted_messages)
        except Exception as ex:
            ex_str = str(ex).lower()
            if any(k in ex_str for k in ["429", "resource_exhausted", "quota", "rate limit", "exceeded"]):
                logger.warning("[AIReasoner] ⚠️ Model hiện tại dính lỗi 429 Quota. Tự động Fallback sang 'gemini-1.5-flash-latest'...")
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    from app.core.config import settings
                    fallback_model = ChatGoogleGenerativeAI(
                        model="gemini-1.5-flash-latest",
                        google_api_key=settings.GEMINI_API_KEY,
                        temperature=0.2,
                        timeout=15.0
                    )
                    response = await fallback_model.ainvoke(formatted_messages)
                except Exception as fallback_ex:
                    logger.error(f"[AIReasoner] Auto-fallback thất bại: {fallback_ex}")
                    raise RuntimeError("⚠️ GEMINI_API_KEY hiện tại đã HẾT QUOTA (Lỗi 429). Vui lòng cập nhật API Key mới vào file .env.")
            else:
                raise ex

        elapsed = time.perf_counter() - start_time
        content = response.content
        result = ""
        if isinstance(content, list):
            result = "".join([block.get("text", "") if isinstance(block, dict) else str(block) for block in content])
        else:
            result = str(content)
            
        last_prompt = messages[-1].content if messages else ""
        usage = getattr(response, "usage_metadata", None)
        self._log_reasoning(system_instruction, str(last_prompt), result, elapsed, usage_metadata=usage)
        return result

    async def astream_reason_with_history(self, messages: list[AnyMessage], system_instruction: str = None):
        """
        Asynchronously stream tokens directly from the LLM using model.astream().
        Yields string chunks live as they arrive from Gemini API.
        """
        formatted_messages = []
        if system_instruction:
            formatted_messages.append(SystemMessage(content=system_instruction))
        formatted_messages.extend(messages)

        start_time = time.perf_counter()
        full_content = []
        try:
            async for chunk in self.model.astream(formatted_messages):
                text_chunk = ""
                if hasattr(chunk, "content"):
                    if isinstance(chunk.content, list):
                        text_chunk = "".join([b.get("text", "") if isinstance(b, dict) else str(b) for b in chunk.content])
                    else:
                        text_chunk = str(chunk.content)
                elif isinstance(chunk, str):
                    text_chunk = chunk
                
                if text_chunk:
                    full_content.append(text_chunk)
                    yield text_chunk
        except Exception as ex:
            ex_str = str(ex).lower()
            if any(k in ex_str for k in ["429", "resource_exhausted", "quota", "rate limit", "exceeded"]):
                logger.warning("[AIReasoner] ⚠️ Model astream dính 429 Quota. Fallback sang 'gemini-1.5-flash-latest'...")
                from langchain_google_genai import ChatGoogleGenerativeAI
                from app.core.config import settings
                fallback_model = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash-latest",
                    google_api_key=settings.GEMINI_API_KEY,
                    temperature=0.2,
                    timeout=15.0
                )
                async for chunk in fallback_model.astream(formatted_messages):
                    text_chunk = str(chunk.content) if hasattr(chunk, "content") else str(chunk)
                    if text_chunk:
                        full_content.append(text_chunk)
                        yield text_chunk
            else:
                raise ex

        elapsed = time.perf_counter() - start_time
        last_prompt = messages[-1].content if messages else ""
        self._log_reasoning(system_instruction, str(last_prompt), "".join(full_content), elapsed)

