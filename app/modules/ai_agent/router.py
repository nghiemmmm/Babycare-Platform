from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.modules.auth.dependencies import get_current_user
from firebase_admin.auth import UserRecord
from app.AI_agents.orchestrator.agent_orchestrator import AgentOrchestrator

ai_agent_router = APIRouter(prefix="/ai", tags=["AI Agent"])

class ChatRequest(BaseModel):
    message: str
    baby_id: Optional[str] = None
    thread_id: str

class ChatResponse(BaseModel):
    response: str
    next_step: Optional[str] = None

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
