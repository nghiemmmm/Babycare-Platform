import os
import time
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from typing import Optional
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage
import logging
from langsmith import traceable
from app.core.config import settings

from app.AI_agents.llmops.observability.timeout import TimeoutConfig
from app.AI_agents.core.constant import DEFAULT_CHAT_MODEL, DEFAULT_TEMPERATURE
from app.AI_agents.context.token_budget import MODEL_PRICING

logger = logging.getLogger(__name__)

class AIReasoner:
    def __init__(self, model_name: str = None, temperature: float = DEFAULT_TEMPERATURE, provider: str = None):
        from app.AI_agents.providers.model_router import ModelRouter

        self.model_name = model_name or settings.OPENROUTER_MODEL or DEFAULT_CHAT_MODEL
        self.provider = provider

        from app.AI_agents.llmops.observability.tracing import get_tracer_callbacks
        callbacks = get_tracer_callbacks()

        self.model = ModelRouter.get_model(
            model_name=self.model_name,
            provider=self.provider,
            temperature=temperature,
            callbacks=callbacks if callbacks else None
        )

    @staticmethod
    def parse_usage_metadata(usage_metadata: Optional[dict]) -> Dict[str, Any]:
        """
        Bóc tách chuẩn hóa token metadata từ các LLM Providers:
        - Gemini native: cached_content_token_count
        - OpenRouter / OpenAI: prompt_tokens_details.cached_tokens
        """
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        cached_tokens = 0

        if usage_metadata and isinstance(usage_metadata, dict):
            prompt_tokens = (
                usage_metadata.get("input_tokens")
                or usage_metadata.get("prompt_tokens")
                or usage_metadata.get("prompt_token_count")
                or 0
            )
            completion_tokens = (
                usage_metadata.get("output_tokens")
                or usage_metadata.get("completion_tokens")
                or usage_metadata.get("candidates_token_count")
                or 0
            )
            total_tokens = (
                usage_metadata.get("total_tokens")
                or usage_metadata.get("total_token_count")
                or (prompt_tokens + completion_tokens)
            )


            # Gemini API format
            if "cached_content_token_count" in usage_metadata:
                cached_tokens = usage_metadata.get("cached_content_token_count") or 0
            # OpenRouter / OpenAI format
            elif "prompt_tokens_details" in usage_metadata and isinstance(usage_metadata["prompt_tokens_details"], dict):
                cached_tokens = usage_metadata["prompt_tokens_details"].get("cached_tokens") or 0
            elif "cached_tokens" in usage_metadata:
                cached_tokens = usage_metadata.get("cached_tokens") or 0

        cached_ratio_pct = round((cached_tokens / prompt_tokens * 100), 2) if prompt_tokens > 0 else 0.0

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cached_tokens": cached_tokens,
            "cached_token_ratio_pct": cached_ratio_pct
        }

    def _log_reasoning(
        self,
        system_instruction: Optional[str],
        prompt: str,
        response_text: str,
        elapsed: float,
        usage_metadata: Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        Ghi log Observability & Token Metrics qua LLMOps Engine.
        """
        parsed = self.parse_usage_metadata(usage_metadata)
        prompt_tokens = parsed["prompt_tokens"]
        completion_tokens = parsed["completion_tokens"]
        total_tokens = parsed["total_tokens"]
        cached_tokens = parsed["cached_tokens"]
        cached_ratio_pct = parsed["cached_token_ratio_pct"]

        if not total_tokens:
            prompt_tokens = int(len((prompt or "").split()) * 1.3) + int(len((system_instruction or "").split()) * 1.3)
            completion_tokens = int(len((response_text or "").split()) * 1.3)
            total_tokens = prompt_tokens + completion_tokens
            parsed["prompt_tokens"] = prompt_tokens
            parsed["completion_tokens"] = completion_tokens
            parsed["total_tokens"] = total_tokens

        try:
            from app.shared.context import get_current_trace_id
            trace_id = get_current_trace_id()
            logger.info(
                f"[AIReasoner] [Trace: {trace_id}] Model: '{self.model_name}' | "
                f"Input Tokens: {prompt_tokens} (Cached: {cached_tokens} / {cached_ratio_pct}%) | "
                f"Output Tokens: {completion_tokens} | Total: {total_tokens} | Elapsed: {elapsed:.2f}s"
            )
        except Exception as e:
            logger.warning(f"[AIReasoner] Failed to log reasoning stats: {e}")

        return parsed


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

    @traceable(name="LLM.areason")
    async def areason(self, prompt: str, system_instruction: str = None) -> str:
        """
        Thực hiện suy luận bất đồng bộ với LLM cho một prompt đơn lẻ.

        Args:
            prompt (str): Nội dung prompt hoặc câu hỏi cần xử lý.
            system_instruction (Optional[str]): Chỉ dẫn hệ thống / Persona cho LLM.

        Returns:
            str: Nội dung văn bản câu trả lời hoàn chỉnh từ LLM.

        Raises:
            RuntimeError: Khi gặp lỗi Rate Limit (429) và toàn bộ fallback model đều hết Quota.
            Exception: Các lỗi kết nối hoặc ngoại lệ từ nhà cung cấp LLM nếu không thể khắc phục.
        """
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
                logger.warning("[AIReasoner] ⚠️ Model hiện tại dính lỗi 429 Quota. Tự động Fallback sang 'gemini-flash-latest'...")
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    from app.core.config import settings
                    fallback_model = ChatGoogleGenerativeAI(
                        model="gemini-flash-latest",
                        google_api_key=settings.GEMINI_API_KEY,
                        temperature=0.2,
                        timeout=TimeoutConfig.REASONER_AGENT_TIMEOUT
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

    @traceable(name="LLM.areason_with_history")
    async def areason_with_history(self, messages: list[AnyMessage], system_instruction: str = None) -> str:
        """
        Thực hiện suy luận bất đồng bộ với LLM kèm toàn bộ lịch sử hội thoại nhiều lượt (Multi-turn History).

        Args:
            messages (list[AnyMessage]): Danh sách các tin nhắn trước đó (HumanMessage, AIMessage).
            system_instruction (Optional[str]): Chỉ dẫn hệ thống / Persona định hình phong cách phản hồi.

        Returns:
            str: Nội dung câu trả lời hoàn chỉnh từ LLM đã được ghi nhận token usage và observability.

        Raises:
            RuntimeError: Khi gặp lỗi Rate Limit (429) và toàn bộ fallback model đều hết Quota.
            Exception: Ngoại lệ không thể xử lý từ nhà cung cấp LLM.
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
                        timeout=TimeoutConfig.REASONER_AGENT_TIMEOUT
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

    @traceable(name="LLM.astream_reason_with_history")
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

