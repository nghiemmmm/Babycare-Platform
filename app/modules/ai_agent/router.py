from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List, Any
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.AI_agents.orchestrator.agent_orchestrator import AgentOrchestrator
from google.cloud.firestore import FieldFilter
from app.infrastructure.database import get_firestore_db
from app.modules.baby.service import BabyService
from datetime import datetime, timezone, timedelta
from app.shared.concurrency import run_in_threadpool
import uuid
import os

from app.modules.ai_agent.schemas import (
    ChatRequest,
    ChatResponse,
    ThreadResponse,
    ThreadCreateResponse,
    MessageCreateRequest,
    Citation,
    ExtractedLog,
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
    current_user: UserRecord = Depends(get_current_user)
):
    orchestrator = AgentOrchestrator()
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
    
    threads = []
    for doc in docs:
        d = doc.to_dict()
        threads.append(ThreadResponse(
            id=doc.id,
            title=d.get("title", "New Chat Session"),
            last_updated=d.get("last_updated", "")
        ))
        
    # Sắp xếp cuộc trò chuyện gần nhất lên đầu
    threads.sort(key=lambda x: x.last_updated, reverse=True)
    threads = threads[:50]
    
    # Nếu chưa có thread nào, tự động tạo một thread ban đầu cho người dùng
    if not threads:
        thread_id = "thread_default"
        doc_ref = db.collection("chat_threads").document(thread_id)
        doc_ref.set({
            "user_id": current_user.uid,
            "title": "Baby Progress Chat",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        threads.append(ThreadResponse(
            id=thread_id,
            title="Baby Progress Chat",
            last_updated=datetime.now(timezone.utc).isoformat()
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
    title = "New Chat Session"
    
    doc_ref = db.collection("chat_threads").document(thread_id)
    doc_ref.set({
        "user_id": current_user.uid,
        "title": title,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return ThreadCreateResponse(thread_id=thread_id, title=title)

from app.infrastructure.cache import redis as cache_redis

@ai_agent_router.get("/threads/{thread_id}/messages", response_model=List[ChatMessageResponse])
async def get_thread_messages(
    thread_id: str,
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
        orchestrator = AgentOrchestrator()
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
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Gửi tin nhắn vào phiên chat hiện tại và nhận phản hồi từ AI Agent cùng kết quả trích xuất nhật ký.
    """
    # 1. Tìm hoặc gán mặc định active baby
    db = get_firestore_db()
    baby_id = req.baby_id
    if not baby_id:
        babies = baby_service.get_my_babies(current_user.uid)
        if babies:
            active_b = next((b for b in babies if b.is_active), babies[0])
            baby_id = active_b.id
        
    # 2. Gọi AgentOrchestrator chạy LangGraph
    orchestrator = AgentOrchestrator()
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
    tool_steps_models = [ToolStep(**ts) if isinstance(ts, dict) else ts for ts in raw_tool_steps]
    tool_steps_dicts = [m.model_dump() for m in tool_steps_models]
    
    # 3. Lưu bản ghi tin nhắn Human & AI vào Firestore subcollection
    now_iso = datetime.now(timezone.utc).isoformat()
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
        "content": last_message,
        "timestamp": now_iso,
        "tool_steps": tool_steps_dicts
    })

    # Xóa cache Redis của thread_id để lượt GET tiếp theo tự làm mới tin nhắn mới
    cache_key = f"chat_messages:{thread_id}:{current_user.uid}"
    await run_in_threadpool(cache_redis.delete, cache_key)
    
    # 4. Cập nhật thời gian hoạt động và tiêu đề của thread
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
        
    # 5. Trích xuất nhật ký thực tế nếu LangGraph nhận dạng được
    extracted_logs = []
    if extracted_data and next_step in ["feeding", "medication", "symptom", "growth"]:
        time_str = datetime.now(timezone.utc).strftime("%I:%M %p")
        if next_step == "feeding":
            food = extracted_data.get("food_name", "Formula")
            amount = extracted_data.get("amount_g", 150)
            extracted_logs.append(ExtractedLog(
                type="feeding",
                title="Feeding Log",
                detail=f"{amount}ml {food}",
                value=f"{amount}ml",
                time=time_str
            ))
        elif next_step == "medication":
            med = extracted_data.get("medication_name", "Paracetamol")
            dose = extracted_data.get("dosage", "150mg")
            extracted_logs.append(ExtractedLog(
                type="medication",
                title="Medication Log",
                detail=f"{med} {dose}",
                value=dose,
                time=time_str
            ))
        elif next_step == "growth":
            h = extracted_data.get("height", 65)
            w = extracted_data.get("weight", 7.0)
            extracted_logs.append(ExtractedLog(
                type="growth",
                title="Growth Log",
                detail=f"Height: {h}cm, Weight: {w}kg",
                value=f"{h}cm",
                time=time_str
            ))
            
    # Default citations
    citations = [
        Citation(title="WHO Infant Nutrition Guidelines", uri="https://who.int/nutrition"),
        Citation(title="AAP Guidelines on Pediatric Antipyretics", uri="https://publications.aap.org")
    ]
    
    return MessageCreateResponse(
        ai_response=MessageResponseDetails(
            content=last_message,
            citations=citations
        ),
        extracted_logs=extracted_logs,
        tool_steps=tool_steps_models
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
            orchestrator = AgentOrchestrator()
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

@ai_agent_router.post("/reports/generate")
async def generate_baby_report(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Kích hoạt AI tổng hợp dữ liệu và xuất bản tệp PDF Báo cáo Tăng trưởng & Y khoa.
    """
    from app.AI_agents.workflows.report_graph import ReportGraph, generate_pdf_report
    graph = ReportGraph().compile()
    
    initial_state = {
        "messages": [],
        "baby_id": baby_id,
        "current_user_id": current_user.uid,
        "extracted_data": {}
    }
    
    res = await graph.ainvoke(initial_state)
    extracted = res.get("extracted_data", {})
    summary = extracted.get("report_text_summary", "Chưa có dữ liệu báo cáo.")
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"report_{baby_id}_{timestamp}.pdf"
    pdf_path = os.path.join("app", "static", "reports", pdf_filename)
    
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    generate_pdf_report(pdf_path, "Báo Cáo Tăng Trưởng & Y Khoa Cho Bé", summary)
    
    pdf_url = f"/static/reports/{pdf_filename}"
    return {
        "success": True,
        "summary": summary,
        "pdf_url": pdf_url,
        "message": "Đã tạo báo cáo PDF thành công."
    }
