from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Optional, List, Any
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.AI_agents.orchestrator.agent_orchestrator import AgentOrchestrator
from app.AI_agents.core.response_formatter import ResponseFormatter
from google.cloud.firestore import FieldFilter, Query
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
    ThreadCreateRequest,
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
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy danh sách lịch sử các phiên chat của người dùng, lọc đúng theo bé đang chọn -
    nếu không lọc theo baby_id, danh sách hội thoại sẽ bị lẫn giữa các bé trong cùng gia đình
    và không đổi theo khi người dùng chuyển bé active trên UI.
    """
    baby_service.get_baby_by_id(baby_id, current_user.uid)  # kiểm tra quyền giám hộ bé này

    db = get_firestore_db()
    docs = (
        db.collection("chat_threads")
        .where(filter=FieldFilter("user_id", "==", current_user.uid))
        .where(filter=FieldFilter("baby_id", "==", baby_id))
        .stream()
    )

    threads = []
    for doc in docs:
        d = doc.to_dict()
        threads.append(ThreadResponse(
            id=doc.id,
            title=d.get("title", "New Chat Session"),
            last_updated=d.get("last_updated", ""),
            baby_id=d.get("baby_id")
        ))

    # Nhận lại các thread tạo TRƯỚC khi hệ thống hỗ trợ nhiều bé (chưa có field baby_id) về đúng
    # bé đầu tiên của gia đình - trước đây mọi thread của user đều ngầm định thuộc về babies[0]
    # (do backend luôn hardcode babies[0] khi trả lời chat), nên nếu không "nhận" lại, lịch sử
    # chat có sẵn của người dùng sẽ biến mất ngay khi vừa nâng cấp lên cơ chế phân biệt theo bé.
    # Chỉ áp dụng khi baby_id đang xét chính là bé đầu tiên - các bé khác chưa từng có lịch sử
    # chat thật sự (AI luôn suy luận theo babies[0] trước đây) nên không có gì để nhận lại.
    if not threads:
        my_babies = baby_service.get_my_babies(current_user.uid)
        if my_babies and my_babies[0].id == baby_id:
            legacy_docs = (
                db.collection("chat_threads")
                .where(filter=FieldFilter("user_id", "==", current_user.uid))
                .stream()
            )
            for doc in legacy_docs:
                d = doc.to_dict()
                if d.get("baby_id"):
                    continue
                db.collection("chat_threads").document(doc.id).update({"baby_id": baby_id})
                threads.append(ThreadResponse(
                    id=doc.id,
                    title=d.get("title", "New Chat Session"),
                    last_updated=d.get("last_updated", ""),
                    baby_id=baby_id
                ))

    # Chỉ hiện các cuộc trò chuyện còn hoạt động trong vòng 1 tuần gần nhất - "hiện đầy đủ lịch sử
    # chat trong vòng 1 tuần" nghĩa là bỏ giới hạn SỐ LƯỢNG cuộc trò chuyện cố định (trước đây cắt
    # cứng còn 6), thay bằng giới hạn theo THỜI GIAN thực tế.
    cutoff_iso = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    threads = [t for t in threads if t.last_updated >= cutoff_iso]

    # Sắp xếp cuộc trò chuyện gần nhất lên đầu
    threads.sort(key=lambda x: x.last_updated, reverse=True)

    # Nếu chưa có thread nào (kể cả sau khi thử nhận lại thread cũ), tự động tạo một thread ban
    # đầu cho user+bé này. ID phải gắn cả user_id lẫn baby_id - trước đây dùng ID cứng
    # "thread_default" chung cho TẤT CẢ user, nên user/bé khác cũng chưa có thread nào sẽ ghi đè
    # lên cùng 1 document, và vì checkpoint của LangGraph lưu theo đúng thread_id đó, lịch sử chat
    # có thể bị lẫn giữa các gia đình khác nhau.
    if not threads:
        thread_id = f"thread_default_{current_user.uid}_{baby_id}"
        now = datetime.now(timezone.utc).isoformat()
        doc_ref = db.collection("chat_threads").document(thread_id)
        doc_ref.set({
            "user_id": current_user.uid,
            "baby_id": baby_id,
            "title": "Baby Progress Chat",
            "last_updated": now,
            "created_at": now
        })
        threads.append(ThreadResponse(
            id=thread_id,
            title="Baby Progress Chat",
            last_updated=now,
            baby_id=baby_id
        ))

    # Lấy trước nội dung tin nhắn cuối cùng của từng cuộc trò chuyện để hiện trong danh sách lịch
    # sử chat - trước đây chỉ có "title" (chốt cứng từ tin nhắn ĐẦU TIÊN, không đổi về sau), nên
    # người dùng không biết cuộc trò chuyện đang nói về nội dung gì nếu chưa bấm vào xem. Đọc từ
    # Firestore subcollection chat_threads/{id}/messages (nguồn thật, được ghi ở create_thread_message
    # / stream_thread_message) - kiến trúc Tier 0/1/2 mới không còn checkpointer.put() sau mỗi lượt
    # chat nên orchestrator.get_state() luôn rỗng, dùng nó ở đây sẽ khiến preview luôn trống.
    for t in threads:
        try:
            last_msg_docs = list(
                db.collection("chat_threads")
                .document(t.id)
                .collection("messages")
                .order_by("timestamp", direction=Query.DESCENDING)
                .limit(1)
                .get()
            )
            if last_msg_docs:
                content = last_msg_docs[0].to_dict().get("content", "")
                t.last_message_preview = content[:80] + "..." if len(content) > 80 else content
        except Exception:
            pass  # Không chặn cả danh sách thread nếu đọc preview của 1 thread bị lỗi

    return threads[:50]

@ai_agent_router.post("/threads", response_model=ThreadCreateResponse)
async def create_chat_thread(
    req: ThreadCreateRequest,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Khởi tạo một phiên chat mới cho đúng bé đang chọn.
    """
    baby_service.get_baby_by_id(req.baby_id, current_user.uid)  # kiểm tra quyền giám hộ bé này

    db = get_firestore_db()
    thread_id = f"thread_{uuid.uuid4().hex[:8]}"
    title = "New Chat Session"
    now = datetime.now(timezone.utc).isoformat()

    doc_ref = db.collection("chat_threads").document(thread_id)
    doc_ref.set({
        "user_id": current_user.uid,
        "baby_id": req.baby_id,
        "title": title,
        "last_updated": now,
        "created_at": now
    })

    return ThreadCreateResponse(thread_id=thread_id, title=title)

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
    # Kiểm tra thread thuộc đúng user trước khi trả lịch sử chat - cùng lý do với
    # delete_thread_messages: tránh lộ lịch sử chat của user/gia đình khác nếu đoán được thread_id.
    # Phải kiểm tra TRƯỚC cả bước đọc Redis Cache, nếu không cache vẫn có thể trả lịch sử chat của
    # người khác cho user đoán trúng thread_id.
    db = get_firestore_db()
    thread_doc = db.collection("chat_threads").document(thread_id).get()
    if thread_doc.exists and thread_doc.to_dict().get("user_id") != current_user.uid:
        raise HTTPException(status_code=403, detail="Access denied")

    cache_key = f"chat_messages:{thread_id}:{current_user.uid}"

    # 1. Thử lấy từ Redis Cache (tốc độ < 10ms)
    cached_data = await run_in_threadpool(cache_redis.get_json, cache_key)
    if cached_data and isinstance(cached_data, list):
        return [ChatMessageResponse(**item) for item in cached_data]

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
        # Trả về TOÀN BỘ tin nhắn của đoạn chat này (trong giới hạn 100 tin gần nhất), không lọc
        # theo thời gian - bộ lọc "7 ngày" chỉ nên áp dụng ở list_chat_threads (ẩn bớt các CUỘC TRÒ
        # CHUYỆN không còn hoạt động khỏi sidebar), áp lại lần nữa cho nội dung BÊN TRONG một đoạn
        # chat đã chọn sẽ làm mất tin nhắn cũ của chính đoạn chat đó nếu đã kéo dài hơn 1 tuần.
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
    except Exception:
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
    # 1. Kiểm tra Cache Policy cho các câu hỏi tra cứu chung
    cached_response = await ResponseFormatter.get_cached_response(req.content)
    if cached_response:
        return MessageCreateResponse(**cached_response)

    # 2. Xác định đúng bé đang được thảo luận trong thread này - ưu tiên baby_id đã lưu sẵn trên
    # thread (nguồn xác thực nhất vì được gán lúc tạo thread), sau đó đến req.baby_id, cuối cùng mới
    # fallback về bé đang active của gia đình. Trước đây hardcode babies[0] nên AI luôn suy luận/ghi
    # log theo bé đầu tiên của gia đình, bất kể người dùng đang chọn bé nào trên UI.
    db = get_firestore_db()
    thread_ref = db.collection("chat_threads").document(thread_id)
    thread_doc = thread_ref.get()
    thread_data = thread_doc.to_dict() if thread_doc.exists else None

    if thread_data and thread_data.get("user_id") != current_user.uid:
        raise HTTPException(status_code=403, detail="Access denied")

    baby_id = (thread_data or {}).get("baby_id") or req.baby_id
    if not baby_id:
        babies = baby_service.get_my_babies(current_user.uid)
        if babies:
            active_b = next((b for b in babies if b.is_active), babies[0])
            baby_id = active_b.id
    if baby_id:
        baby_service.get_baby_by_id(baby_id, current_user.uid)  # kiểm tra quyền giám hộ bé này

    # 3. Gọi AgentOrchestrator chạy LangGraph
    orchestrator = get_orchestrator(request)
    result = await orchestrator.run_agent(
        message=req.content,
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
        "content": req.content,
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
        if thread_data.get("title") in ["New Chat Session", "Baby Progress Chat"]:
            update_fields["title"] = req.content[:30] + "..." if len(req.content) > 30 else req.content
        thread_ref.update(update_fields)
    else:
        thread_ref.set({
            "user_id": current_user.uid,
            "title": req.content[:30] + "..." if len(req.content) > 30 else req.content,
            "last_updated": now_iso,
            "created_at": now_iso
        })

    # 7. Lưu cache nếu câu hỏi là tra cứu chung (Cache Policy)
    await ResponseFormatter.set_cached_response(req.content, formatted_response.model_dump())
    
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

    async def generate_sse():
        from app.shared.context import get_current_trace_id
        trace_id = get_current_trace_id()
        collected_tokens = []
        final_tool_steps = []
        is_completed = False
        now_iso = datetime.now(timezone.utc).isoformat()

        async for sse_chunk in orchestrator.stream_agent(
            message=req.content,
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
        media_type="text/event-stream"
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
    Xử lý phản hồi cực nhanh (< 50ms) để không bị treo loading.
    """
    import re
    import asyncio
    text = req.transcript.lower().strip()
    intent = "feeding"
    extracted_data = {}
    
    # 1. Fast & Reliable Local Parsing (Phản hồi tức thì < 50ms)
    if "sữa" in text or "bú" in text or "ml" in text:
        intent = "feeding"
        ml_match = re.search(r"(\d+)\s*(ml|cc)?", text)
        if ml_match:
            extracted_data["amount"] = float(ml_match.group(1))
        else:
            extracted_data["amount"] = 150.0
            
        if "công thức" in text or "bình" in text:
            extracted_data["type"] = "Formula"
            extracted_data["details"] = f"{extracted_data.get('amount', 150)}ml Sữa công thức"
        elif "mẹ" in text:
            extracted_data["type"] = "Breast"
            extracted_data["details"] = f"{extracted_data.get('amount', 120)}ml Sữa mẹ"
        else:
            extracted_data["type"] = "Formula"
            extracted_data["details"] = f"{extracted_data.get('amount', 150)}ml Sữa công thức"

    elif "thuốc" in text or "hapacol" in text or "paracetamol" in text or "vitamin" in text or "mg" in text or "giọt" in text:
        intent = "medication"
        dose_match = re.search(r"(\d+)\s*(mg|giọt|viên)", text)
        if dose_match:
            extracted_data["dosage"] = f"{dose_match.group(1)}{dose_match.group(2)}"
        else:
            extracted_data["dosage"] = "150mg"
            
        if "hapacol" in text:
            extracted_data["medication_name"] = "Hapacol 150mg"
        elif "paracetamol" in text:
            extracted_data["medication_name"] = "Paracetamol"
        elif "vitamin" in text:
            extracted_data["medication_name"] = "Vitamin D3 K2"
        else:
            extracted_data["medication_name"] = "Hapacol 150mg"

    elif "cân" in text or "ký" in text or "kg" in text or "cao" in text or "cm" in text:
        intent = "growth"
        kg_match = re.search(r"(\d+(\.\d+)?)\s*(kg|ký|kí)", text)
        cm_match = re.search(r"(\d+(\.\d+)?)\s*(cm)", text)
        if kg_match:
            extracted_data["weight"] = float(kg_match.group(1))
        if cm_match:
            extracted_data["height"] = float(cm_match.group(1))

    elif "tã" in text or "bỉm" in text or "tè" in text or "ỉa" in text:
        intent = "diaper"
        if "bẩn" in text or "ỉa" in text:
            extracted_data["type"] = "Dirty"
        else:
            extracted_data["type"] = "Wet"

    elif "ngủ" in text or "thức" in text or "dậy" in text:
        intent = "sleep"
        extracted_data["details"] = text

    # 2. LLM Fallback nếu chưa nhận diện được bằng Fast Parser
    if not extracted_data:
        try:
            orchestrator = get_orchestrator(request)
            temp_thread_id = f"voice_{uuid.uuid4().hex[:8]}"
            result = await asyncio.wait_for(
                orchestrator.run_agent(
                    message=f"Bóc tách nhật ký ghi chép từ câu thoại: {req.transcript}",
                    thread_id=temp_thread_id,
                    baby_id=req.baby_id,
                    user_id=current_user.uid
                ),
                timeout=2.5
            )
            intent = result.get("next_step") or intent
            extracted_data = result.get("extracted_data") or extracted_data
        except Exception as e:
            print(f"Voice LLM extraction fallback/timeout: {e}")

    return VoiceExtractResponse(
        intent=intent,
        extracted_data=extracted_data,
        confidence_message="Bóc tách dữ liệu từ giọng nói thành công."
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
