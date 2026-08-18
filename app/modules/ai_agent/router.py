from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Optional, List, Any
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.AI_agents.orchestrator.agent_orchestrator import AgentOrchestrator
from app.AI_agents.core.response_formatter import ResponseFormatter
from google.cloud.firestore import FieldFilter
from app.infrastructure.database import get_firestore_db
from app.modules.baby.service import BabyService
from datetime import datetime, timezone, timedelta
from app.shared.concurrency import run_in_threadpool
from app.shared.jobs import JobManager, JobStatus
from app.shared.schemas import AsyncJobCreatedResponse
import logging
import uuid
import os
import asyncio

logger = logging.getLogger(__name__)




def get_orchestrator(request: Request) -> AgentOrchestrator:
    """
    Lấy AgentOrchestrator singleton từ app.state.
    Fallback: tạo mới nếu chưa được khởi tạo trong lifespan (dev / testing).
    """
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if orchestrator is None:
        orchestrator = AgentOrchestrator()
    return orchestrator

from app.modules.ai_agent.schemas import (
    ChatRequest,
    ChatResponse,
    ThreadResponse,
    ThreadCreateResponse,
    MessageCreateRequest,
    Citation,
    ExtractedLog,
    ToolStep,
    MessageResponseDetails,
    MessageCreateResponse,
    SleepTimerRequest,
    SleepTimerResponse,
    ChatMessageResponse,
    VoiceExtractRequest,
    VoiceExtractResponse
)

ai_agent_router = APIRouter(prefix="/ai", tags=["AI Agent"])
baby_service = BabyService()

@ai_agent_router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    req: ChatRequest,
    request: Request,
    current_user: UserRecord = Depends(get_current_user)
):
    orchestrator = get_orchestrator(request)
    result = await orchestrator.run_agent(
        message=req.message,
        thread_id=req.thread_id,
        baby_id=req.baby_id,
        user_id=current_user.uid
    )
    
    last_message = result["messages"][-1].content
    next_step = result.get("next_step")
    
    return ChatResponse(
        response=last_message,
        next_step=next_step
    )


@ai_agent_router.get("/threads", response_model=List[ThreadResponse])
async def list_chat_threads(
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy danh sách lịch sử các phiên chat của người dùng.
    """
    db = get_firestore_db()
    docs = db.collection("chat_threads").where(filter=FieldFilter("user_id", "==", current_user.uid)).stream()
    
    now_iso = datetime.now(timezone.utc).isoformat()
    threads = []
    for doc in docs:
        d = doc.to_dict()
        created_at = d.get("created_at") or d.get("last_updated") or now_iso
        updated_at = d.get("updated_at") or d.get("last_updated") or now_iso
        threads.append(ThreadResponse(
            thread_id=doc.id,
            id=doc.id,
            title=d.get("title", "Cuộc trò chuyện mới"),
            created_at=created_at,
            updated_at=updated_at,
            last_updated=updated_at,
            baby_id=d.get("baby_id")
        ))

        
    # Sắp xếp cuộc trò chuyện gần nhất lên đầu
    threads.sort(key=lambda x: x.updated_at, reverse=True)
    threads = threads[:50]
    
    # Nếu chưa có thread nào, tự động tạo một thread ban đầu cho người dùng
    if not threads:
        thread_id = f"thread_{current_user.uid[:8]}_default"
        doc_ref = db.collection("chat_threads").document(thread_id)
        doc_ref.set({
            "user_id": current_user.uid,
            "title": "Tư vấn chăm sóc bé",
            "created_at": now_iso,
            "updated_at": now_iso
        })
        threads.append(ThreadResponse(
            thread_id=thread_id,
            title="Tư vấn chăm sóc bé",
            created_at=now_iso,
            updated_at=now_iso
        ))
        
    return threads[:50]


@ai_agent_router.post("/threads", response_model=ThreadCreateResponse)
async def create_chat_thread(
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Khởi tạo một phiên chat mới.
    """
    db = get_firestore_db()
    thread_id = f"thread_{uuid.uuid4().hex[:8]}"
    title = "Cuộc trò chuyện mới"
    now_iso = datetime.now(timezone.utc).isoformat()
    
    doc_ref = db.collection("chat_threads").document(thread_id)
    doc_ref.set({
        "user_id": current_user.uid,
        "title": title,
        "last_updated": now_iso,
        "created_at": now_iso
    })
    
    return ThreadCreateResponse(
        thread_id=thread_id,
        id=thread_id,
        title=title,
        created_at=now_iso
    )


from app.infrastructure.cache import redis as cache_redis

@ai_agent_router.get("/threads/{thread_id}/messages", response_model=List[ChatMessageResponse])
async def get_thread_messages(
    thread_id: str,
    request: Request,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy danh sách các tin nhắn trong phiên chat từ Redis Cache, Firestore subcollection, hoặc LangGraph Checkpointer.
    """
    cache_key = f"chat_messages:{thread_id}:{current_user.uid}"
    
    # 1. Thử lấy từ Redis Cache (tốc độ < 10ms)
    cached_data = await run_in_threadpool(cache_redis.get_json, cache_key)
    if cached_data and isinstance(cached_data, list):
        return [ChatMessageResponse(**item) for item in cached_data]

    db = get_firestore_db()

    # 2. Đọc từ Firestore subcollection chat_threads/{thread_id}/messages
    msg_docs = list(
        db.collection("chat_threads")
        .document(thread_id)
        .collection("messages")
        .stream()
    )
    if msg_docs:
        result = []
        for doc in msg_docs:
            d = doc.to_dict()
            result.append(ChatMessageResponse(
                id=doc.id,
                role=d.get("role", "user"),
                content=d.get("content", ""),
                timestamp=d.get("timestamp", datetime.now(timezone.utc).isoformat()),
                tool_steps=d.get("tool_steps", [])
            ))
        result.sort(key=lambda x: x.timestamp)
        final_messages = result[-100:]
        if final_messages:
            serializable = [m.model_dump() for m in final_messages]
            await run_in_threadpool(cache_redis.set_json, cache_key, serializable, 1800)
        return final_messages

    # 3. Fallback: Đọc từ LangGraph Firestore Checkpointer
    messages = []
    try:
        orchestrator = get_orchestrator(request)
        state_dict = await orchestrator.get_state(thread_id, current_user.uid)
        messages = state_dict.get("values", {}).get("messages", [])
    except Exception as e:
        messages = []
    
    result = []
    for msg in messages:
        role = "user" if getattr(msg, "type", "") == "human" else "assistant"
        msg_id = getattr(msg, "id", None) or f"msg_{uuid.uuid4().hex[:8]}"
        
        ts = getattr(msg, "response_metadata", {}).get("created_at") if hasattr(msg, "response_metadata") else None
        if not ts:
            ts = datetime.now(timezone.utc).isoformat()
            
        result.append(ChatMessageResponse(
            id=msg_id,
            role=role,
            content=getattr(msg, "content", str(msg)),
            timestamp=ts
        ))
        
    final_messages = result[-100:]
    
    # Ghi vào Redis Cache với TTL 30 phút (1800s)
    if final_messages:
        serializable = [m.model_dump() for m in final_messages]
        await run_in_threadpool(cache_redis.set_json, cache_key, serializable, 1800)

    return final_messages


@ai_agent_router.post("/threads/{thread_id}/messages", response_model=MessageCreateResponse)
async def create_thread_message(
    thread_id: str,
    req: MessageCreateRequest,
    request: Request,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Gửi tin nhắn vào phiên chat hiện tại và nhận phản hồi từ AI Agent cùng kết quả trích xuất nhật ký.
    Sử dụng ResponseFormatter để chuẩn hóa câu trả lời, bóc tách Citations thật và kiểm tra Grounding/Cache.
    """
    msg_text = req.text_content
    # 1. Kiểm tra Cache Policy cho các câu hỏi tra cứu chung
    cached_response = await ResponseFormatter.get_cached_response(msg_text)
    if cached_response:
        return MessageCreateResponse(**cached_response)

    # 2. Tìm hoặc gán mặc định active baby
    db = get_firestore_db()
    baby_id = req.baby_id
    if not baby_id:
        babies = baby_service.get_my_babies(current_user.uid)
        if babies:
            active_b = next((b for b in babies if b.is_active), babies[0])
            baby_id = active_b.id
        
    # 3. Gọi AgentOrchestrator chạy LangGraph
    orchestrator = get_orchestrator(request)
    result = await orchestrator.run_agent(
        message=msg_text,
        thread_id=thread_id,
        baby_id=baby_id,
        user_id=current_user.uid
    )
    
    last_message = result["messages"][-1].content
    next_step = result.get("next_step")
    extracted_data = result.get("extracted_data")
    raw_tool_steps = result.get("tool_steps", [])
    rag_context = result.get("rag_context")
    
    # 4. Sử dụng ResponseFormatter chuẩn hóa response & citations
    formatted_response = ResponseFormatter.format_unified_response(
        raw_message=last_message,
        rag_context=rag_context,
        extracted_data=extracted_data,
        next_step=next_step,
        raw_tool_steps=raw_tool_steps
    )
    
    # 5. Lưu bản ghi tin nhắn Human & AI vào Firestore subcollection
    now_iso = datetime.now(timezone.utc).isoformat()
    msgs_col = db.collection("chat_threads").document(thread_id).collection("messages")
    user_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
    ai_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
    
    tool_steps_dicts = [m.model_dump() for m in formatted_response.tool_steps]
    msgs_col.document(user_msg_id).set({
        "role": "user",
        "content": msg_text,
        "timestamp": now_iso
    })
    msgs_col.document(ai_msg_id).set({
        "role": "assistant",
        "content": formatted_response.ai_response.content,
        "timestamp": now_iso,
        "tool_steps": tool_steps_dicts
    })

    # Xóa toàn bộ Redis cache rác của em bé (Dashboard, cữ bú, thuốc, chỉ số) để các tab khác tự làm mới
    await run_in_threadpool(cache_redis.invalidate_baby_cache, baby_id, current_user.uid)

    
    # 6. Cập nhật thời gian hoạt động và tiêu đề của thread
    thread_ref = db.collection("chat_threads").document(thread_id)
    if thread_ref.get().exists:
        update_fields = {"last_updated": now_iso}
        thread_data = thread_ref.get().to_dict()
        if thread_data.get("title") in ["New Chat Session", "Cuộc trò chuyện mới", "Baby Progress Chat"]:
            update_fields["title"] = msg_text[:30] + "..." if len(msg_text) > 30 else msg_text
        thread_ref.update(update_fields)
    else:
        thread_ref.set({
            "user_id": current_user.uid,
            "title": msg_text[:30] + "..." if len(msg_text) > 30 else msg_text,
            "last_updated": now_iso,
            "created_at": now_iso
        })

    # 7. Lưu cache nếu câu hỏi là tra cứu chung (Cache Policy)
    await ResponseFormatter.set_cached_response(msg_text, formatted_response.model_dump())
    
    return formatted_response


@ai_agent_router.post("/threads/{thread_id}/stream")
async def stream_thread_message(
    thread_id: str,
    req: MessageCreateRequest,
    request: Request,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Endpoint trả dữ liệu phản hồi dạng W3C SSE Streaming liên tục (text/event-stream).
    Hỗ trợ Idempotency-Key, Run ID, Token delta streaming và disconnect detection.
    """
    idempotency_key = request.headers.get("Idempotency-Key") or request.headers.get("X-Request-ID")
    if idempotency_key:
        cache_key = f"idempotency_stream:{thread_id}:{idempotency_key}"
        if cache_redis.get_json(cache_key):
            logger.info(f"[StreamRoute] Idempotency hit cho key {idempotency_key} - Bỏ qua duplicate execution.")

    db = get_firestore_db()
    baby_id = req.baby_id
    if not baby_id:
        from app.shared.concurrency import run_in_threadpool
        babies = await run_in_threadpool(baby_service.get_my_babies, current_user.uid)
        if babies:
            active_b = next((b for b in babies if b.is_active), babies[0])
            baby_id = active_b.id

    orchestrator = get_orchestrator(request)
    msg_text = req.text_content

    async def generate_sse():
        from app.shared.context import get_current_trace_id
        trace_id = get_current_trace_id()
        collected_tokens = []
        final_tool_steps = []
        is_completed = False
        now_iso = datetime.now(timezone.utc).isoformat()

        async for sse_chunk in orchestrator.stream_agent(
            message=msg_text,
            thread_id=thread_id,
            baby_id=baby_id,
            user_id=current_user.uid
        ):

            if await request.is_disconnected():
                wasted_text = "".join(collected_tokens)
                wasted_tokens = int(len(wasted_text.split()) * 1.3)
                wasted_cost_usd = round((wasted_tokens / 1_000_000.0) * 0.40, 7)
                logger.warning(
                    f"[{trace_id}] ⚠️ Client disconnected mid-stream for thread {thread_id}! "
                    f"Wasted Tokens: {wasted_tokens} | Estimated Wasted Cost: ${wasted_cost_usd} USD"
                )
                break

            yield sse_chunk

            # Parse W3C SSE event data for history tracking
            try:
                lines = sse_chunk.split("\n")
                event_name = ""
                data_str = ""
                for l in lines:
                    if l.startswith("event: "):
                        event_name = l.replace("event: ", "").strip()
                    elif l.startswith("data: "):
                        data_str = l.replace("data: ", "").strip()

                if data_str:
                    payload = json.loads(data_str) if data_str.startswith("{") else data_str
                    if isinstance(payload, dict):
                        if event_name == "response.token" or payload.get("delta"):
                            collected_tokens.append(payload.get("delta", ""))
                        elif event_name == "response.completed" or payload.get("status") == "completed":
                            is_completed = True
                            if payload.get("tool_steps"):
                                final_tool_steps = payload.get("tool_steps", [])
            except Exception:
                pass

        full_ai_content = "".join(collected_tokens).strip() or "Tôi đã ghi nhận thông tin từ mẹ."
        stream_status = "completed" if is_completed else "interrupted"

        async def _save_chat_history_background():
            try:
                from app.shared.concurrency import run_in_threadpool
                def _sync_save():
                    msgs_col = db.collection("chat_threads").document(thread_id).collection("messages")
                    user_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
                    ai_msg_id = f"msg_{uuid.uuid4().hex[:8]}"

                    msgs_col.document(user_msg_id).set({
                        "role": "user",
                        "content": req.content,
                        "timestamp": now_iso
                    })
                    msgs_col.document(ai_msg_id).set({
                        "role": "assistant",
                        "content": full_ai_content,
                        "status": stream_status,
                        "timestamp": now_iso,
                        "tool_steps": final_tool_steps
                    })
                await run_in_threadpool(_sync_save)

                if baby_id:
                    await run_in_threadpool(cache_redis.invalidate_baby_cache, baby_id, current_user.uid)

                if idempotency_key:
                    cache_redis.set_json(f"idempotency_stream:{thread_id}:{idempotency_key}", {"status": stream_status}, 300)
            except Exception as ex:
                logger.warning(f"[StreamRoute] Could not save thread history: {ex}")

        asyncio.create_task(_save_chat_history_background())

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )




@ai_agent_router.post("/sleep/timer", response_model=SleepTimerResponse)
async def handle_sleep_timer(
    req: SleepTimerRequest,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Bấm giờ ngủ của bé (bắt đầu hoặc dừng và lưu log).
    """
    db = get_firestore_db()
    timer_ref = db.collection("sleep_timers").document(req.baby_id)
    
    now_str = datetime.now(timezone.utc).isoformat()
    
    if req.action == "start":
        # Lưu thời điểm bắt đầu đếm
        timer_ref.set({
            "start_time": now_str,
            "user_id": current_user.uid,
            "status": "Running"
        })
        return SleepTimerResponse(
            success=True,
            status="Running",
            start_time=now_str
        )
    else:
        # Dừng và lưu log
        doc = timer_ref.get()
        if not doc.exists:
            # Fallback nếu bấm stop mà chưa có start
            return SleepTimerResponse(
                success=True,
                status="Stopped",
                start_time=now_str
            )
            
        timer_data = doc.to_dict()
        start_time_str = timer_data.get("start_time")
        
        start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
        end_time = datetime.now(timezone.utc)
        
        duration = end_time - start_time
        mins = int(duration.total_seconds() / 60)
        hrs = int(mins / 60)
        mins_rem = mins % 60
        
        duration_str = f"{hrs}h {mins_rem}m" if hrs > 0 else f"{mins_rem}m"
        
        # Lưu bản ghi giấc ngủ vào timeline của bé (lưu vào nutrition_feeds với type='Solids' hoặc tạo log riêng)
        # Frontend hiển thị bộ đếm ngủ trong feeds timeline
        feed_id = f"feed_{uuid.uuid4().hex[:8]}"
        db.collection("nutrition_feeds").document(feed_id).set({
            "baby_id": req.baby_id,
            "type": "Solids",  # Map với UI timeline của bé
            "details": f"Sleep Nap Duration: {duration_str}",
            "amount": 1.0,
            "time": end_time.astimezone().strftime("%I:%M %p"),
            "date": end_time.date().isoformat(),
            "created_at": end_time.isoformat()
        })
        
        # Xoá timer hoạt động
        timer_ref.delete()
        
        return SleepTimerResponse(
            success=True,
            status="Stopped",
            start_time=start_time_str
        )

@ai_agent_router.delete("/threads/{thread_id}")
async def delete_chat_thread(
    thread_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Xóa vĩnh viễn một cuộc trò chuyện (thread) và toàn bộ checkpoints tin nhắn liên quan.
    """
    db = get_firestore_db()
    thread_ref = db.collection("chat_threads").document(thread_id)
    thread_doc = thread_ref.get()
    if thread_doc.exists:
        thread_data = thread_doc.to_dict()
        if thread_data.get("user_id") != current_user.uid:
            raise HTTPException(status_code=403, detail="Access denied")
        thread_ref.delete()

    # Xoá checkpoint của LangGraph trong Firestore
    from app.AI_agents.core.constant import CHECKPOINT_COLLECTION
    docs = db.collection(CHECKPOINT_COLLECTION).where(filter=FieldFilter("thread_id", "==", thread_id)).stream()
    for doc in docs:
        doc.reference.delete()

    return {"success": True, "message": "Đã xóa cuộc trò chuyện thành công."}

@ai_agent_router.delete("/threads/{thread_id}/messages")
async def delete_thread_messages(
    thread_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Xóa toàn bộ tin nhắn/lịch sử chat trong phiên chat này (reset checkpoint).
    """
    db = get_firestore_db()
    # 1. Check if thread exists and belongs to this user
    thread_ref = db.collection("chat_threads").document(thread_id)
    thread_doc = thread_ref.get()
    if thread_doc.exists:
        thread_data = thread_doc.to_dict()
        if thread_data.get("user_id") != current_user.uid:
            raise HTTPException(status_code=403, detail="Access denied")
            
    # 2. Xoá checkpoint của LangGraph trong Firestore
    from app.AI_agents.core.constant import CHECKPOINT_COLLECTION
    docs = db.collection(CHECKPOINT_COLLECTION).where(filter=FieldFilter("thread_id", "==", thread_id)).stream()
    for doc in docs:
        doc.reference.delete()
        
    return {"success": True, "message": "Thread history reset successfully."}


@ai_agent_router.post("/voice-extract", response_model=VoiceExtractResponse)
async def extract_from_voice(
    req: VoiceExtractRequest,
    request: Request,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Bóc tách câu thoại tiếng Việt thu được từ Web Speech API thành dữ liệu cấu trúc
    cho các biểu mẫu ghi chép (sữa, thuốc, tã, ngủ, tăng trưởng).
    Xử lý phản hồi cực nhanh (< 15ms) bằng FastVoiceParser Deterministic Engine.
    """
    from app.AI_agents.core.fast_voice_parser import FastVoiceParser
    import time
    t0 = time.time()
    
    response = FastVoiceParser.parse(transcript=req.transcript, baby_id=req.baby_id)
    duration_ms = int((time.time() - t0) * 1000)
    logger.info(f"🎙️ [VoiceExtract] Intent: {response.intent} | Conf: {response.confidence} | Duration: {duration_ms}ms")
    
    return response


# ─── TEXT-TO-ACTION AUTONOMOUS MULTI-TOOL PIPELINE ───────────────────────────

from pydantic import BaseModel, Field
from app.AI_agents.actions.schemas import (
    ActionExecutionReport,
    ActionParseResponse,
    ActionConfirmRequest,
    ActionResultItem,
    ActionStatus,
    ActionType
)
from app.AI_agents.actions.parser import ActionParserEngine
from app.AI_agents.actions.dispatcher import ActionDispatcher

class VoiceActionRequest(BaseModel):
    text: str = Field(..., description="Câu thoại khẩu lệnh hoặc văn bản nhập liệu")
    baby_id: str

action_dispatcher = ActionDispatcher()

@ai_agent_router.post("/voice-action/parse", response_model=ActionParseResponse)
async def parse_voice_action(
    req: VoiceActionRequest,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Trích xuất các thành phần từ câu thoại giọng nói và trả về để người dùng xem trước & xác nhận.
    Nếu đầy đủ thông số: is_complete = True (hiển thị nút Xác nhận Thêm).
    Nếu thiếu thông số: trả về missing_fields + clarification_prompt + suggested_chips.
    """
    raw_text = req.text.strip()
    actions = ActionParserEngine.parse_actions(text=raw_text, baby_id=req.baby_id)
    
    complete_actions = []
    clarifications = []
    for a in actions:
        if a.status == ActionStatus.NEEDS_CLARIFICATION or len(a.missing_fields) > 0:
            clarifications.append(a)
        else:
            complete_actions.append(a)
            
    is_complete = (len(complete_actions) > 0 and len(clarifications) == 0)
    
    summary_parts = []
    for a in complete_actions:
        if a.action_type == ActionType.CREATE_FEEDING:
            p = a.parameters
            feed_type_name = "Sữa mẹ" if p.get('feed_type') == 'Breast' else ("Sữa công thức" if p.get('feed_type') == 'Formula' else "Ăn dặm")
            summary_parts.append(f"Cữ bú: {p.get('amount', 0)}ml ({feed_type_name})")
        elif a.action_type == ActionType.CREATE_MEDICATION:
            p = a.parameters
            summary_parts.append(f"Uống thuốc: {p.get('medication_name', '')} ({p.get('dosage', '')})")
        elif a.action_type == ActionType.CREATE_SLEEP:
            p = a.parameters
            dur = p.get('duration_minutes')
            summary_parts.append(f"Giấc ngủ: {dur} phút" if dur else "Bắt đầu giấc ngủ")
        elif a.action_type == ActionType.CREATE_DIAPER:
            p = a.parameters
            d_type = "Tè ướt" if p.get('diaper_type') == 'Wet' else ("Đi ngoài bẩn" if p.get('diaper_type') == 'Dirty' else "Cả hai")
            summary_parts.append(f"Thay tã: {d_type}")

    summary_prompt = " • ".join(summary_parts) if summary_parts else None
    
    return ActionParseResponse(
        raw_text=raw_text,
        is_complete=is_complete,
        parsed_actions=complete_actions,
        clarifications=clarifications,
        warnings=[],
        summary_prompt=summary_prompt
    )

@ai_agent_router.post("/voice-action", response_model=ActionExecutionReport)
async def execute_voice_action(
    req: VoiceActionRequest,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Tiếp nhận câu thoại hoặc văn bản, tự động phân tích và thực thi đa hành động (Multi-Tool Calling)
    qua các Business Service chính thức, bảo đảm an toàn y tế và tự động lưu vào database Firestore.
    """
    import time
    t0 = time.time()
    
    # 1. Bóc tách Actions
    actions = ActionParserEngine.parse_actions(text=req.text, baby_id=req.baby_id)
    
    # 2. Điều phối Multi-Tool Execution song song
    report = await action_dispatcher.dispatch(actions=actions, user_id=current_user.uid)
    
    duration_ms = int((time.time() - t0) * 1000)
    logger.info(f"⚡ [VoiceAction] Executed: {len(report.executed_actions)} | Pending: {len(report.pending_confirmations)} | Duration: {duration_ms}ms")
    return report


@ai_agent_router.post("/actions/confirm", response_model=ActionExecutionReport)
async def confirm_action(
    req: ActionConfirmRequest,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Cổng xác nhận Human-in-the-Loop cho các hành động rủi ro cao (ví dụ: cữ uống thuốc).
    """
    if not req.confirmed:
        return ActionExecutionReport(
            success=True,
            summary_message="Đã hủy hành động theo yêu cầu của phụ huynh."
        )
    
    # Thực thi Action đã được phụ huynh xác nhận
    result_item = await action_dispatcher.execute_action(action=req.action, user_id=current_user.uid)
    
    executed = [result_item] if result_item.status == ActionStatus.COMPLETED else []
    failed = [result_item] if result_item.status == ActionStatus.FAILED else []
    
    return ActionExecutionReport(
        success=(len(failed) == 0),
        executed_actions=executed,
        failed_actions=failed,
        summary_message=result_item.message
    )



async def _bg_generate_baby_report(job_id: str, baby_id: str, user_id: str):
    JobManager.update_job(job_id, JobStatus.PROCESSING, progress=20)
    try:
        from app.AI_agents.workflows.report_graph import ReportGraph, generate_pdf_report
        graph = ReportGraph().compile()

        initial_state = {
            "messages": [],
            "baby_id": baby_id,
            "current_user_id": user_id,
            "extracted_data": {}
        }

        res = await graph.ainvoke(initial_state)
        JobManager.update_job(job_id, JobStatus.PROCESSING, progress=70)

        extracted = res.get("extracted_data", {})
        summary = extracted.get("report_text_summary", "Chưa có dữ liệu báo cáo.")

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"report_{baby_id}_{timestamp}.pdf"
        pdf_path = os.path.join("app", "static", "reports", pdf_filename)

        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        generate_pdf_report(pdf_path, "Báo Cáo Tăng Trưởng & Y Khoa Cho Bé", summary)

        pdf_url = f"/static/reports/{pdf_filename}"
        result_payload = {
            "success": True,
            "summary": summary,
            "pdf_url": pdf_url,
            "message": "Nhật ký theo dõi sức khỏe cho bé đã được xuất thành công."
        }
        JobManager.update_job(job_id, JobStatus.COMPLETED, progress=100, result=result_payload)
    except Exception as e:
        logger.error(f"Lỗi tạo báo cáo PDF y khoa trong background (Job {job_id}): {e}")
        JobManager.update_job(job_id, JobStatus.FAILED, error=str(e))


@ai_agent_router.post("/reports/generate", response_model=AsyncJobCreatedResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_baby_report(
    baby_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Kích hoạt AI tổng hợp dữ liệu và xuất bản tệp PDF Báo cáo Tăng trưởng & Y khoa dạng Async Background Job.
    """
    job_id = JobManager.create_job("report_generation", current_user.uid, {"baby_id": baby_id})
    background_tasks.add_task(_bg_generate_baby_report, job_id, baby_id, current_user.uid)

    return AsyncJobCreatedResponse(
        job_id=job_id,
        status="PENDING",
        message="Nhắc nhở tổng hợp báo cáo sức khỏe cho bé đang được xử lý trong nền..."
    )
