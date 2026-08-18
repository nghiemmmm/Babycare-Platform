"""
AI Cry Tracking & Prediction Service Module
===========================================
Handles business logic and executes the Context-Aware Closed-Loop Cry Analysis Pipeline.
Unifies REST API flow with the multi-agent graph architecture.
"""
import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Union
from fastapi import UploadFile, HTTPException, status

from app.modules.cry.schemas import (
    CryLogCreate,
    CryLogResponse,
    CryFeedbackUpdate,
    AudioEvidence,
    CryContextBundle,
    CryDecision,
    AdjustedEvidence
)
from app.modules.cry.repository import CryRepository
from app.modules.baby.service import BabyService
from app.shared.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


class CryService:
    def __init__(self, baby_service: Optional[BabyService] = None):
        self.baby_service = baby_service or BabyService()
        self._graph = None

    @property
    def graph(self):
        if self._graph is None:
            from app.AI_agents.workflows.cry_analysis_graph import CryAnalysisGraph
            self._graph = CryAnalysisGraph()
        return self._graph

    def predict_cry(self, baby_id: str, audio_file: UploadFile, user_id: str) -> CryLogResponse:

        """
        Nhận tệp ghi âm tiếng khóc, thực thi trọn vẹn luồng Context-Aware Closed-Loop Pipeline:
        Audio → AST → Multi-Context → Explicit Fusion → Safety Gate → Policy Engine → LLM Explanation → Firestore.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = CryRepository(baby_id)

        # Lưu tệp ghi âm vào thư mục app/static/cry
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "cry")
        os.makedirs(upload_dir, exist_ok=True)

        raw_filename = audio_file.filename or "audio.wav"
        safe_filename = raw_filename.replace(" ", "_")
        timestamp_prefix = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        saved_filename = f"{timestamp_prefix}_{safe_filename}"
        audio_file_path = os.path.join(upload_dir, saved_filename)

        content = audio_file.file.read()
        with open(audio_file_path, "wb") as f:
            f.write(content)

        audio_url = f"/static/cry/{saved_filename}"

        # ── THỰC THI PIPELINE ĐỒ THỊ CLOSED-LOOP ───────────────────────────
        try:
            initial_state = {
                "messages": [],
                "baby_id": baby_id,
                "current_user_id": user_id,
                "extracted_data": {
                    "audio_file": audio_file_path
                }
            }

            async def run_pipeline():
                app_graph = self.graph.compile()
                return await app_graph.ainvoke(initial_state)

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                    final_state = loop.run_until_complete(run_pipeline())
                else:
                    final_state = asyncio.run(run_pipeline())
            except Exception:
                final_state = asyncio.run(run_pipeline())

            ext_data = final_state.get("extracted_data", {})
            
            raw_audio_evidence = ext_data.get("audio_evidence", {})
            audio_evidence = AudioEvidence(**raw_audio_evidence) if raw_audio_evidence else None
            
            raw_context = ext_data.get("cry_context", {})
            context_bundle = CryContextBundle(**raw_context) if raw_context else None
            
            raw_decision = ext_data.get("cry_decision", {})
            decision = CryDecision(**raw_decision) if raw_decision else None

            advice_text = ext_data.get("advice") or (final_state.get("messages")[-1].content if final_state.get("messages") else "")
            
            prediction = decision.primary_cause if decision else ext_data.get("cry_prediction", "unknown")
            confidence = decision.adjusted_confidence if decision else ext_data.get("cry_confidence", 0.0)
            reason_scores = ext_data.get("reason_scores", {})
            sound_played = decision.soothing_sound if decision else ext_data.get("soothing_sound")
            sound_conditioned = (sound_played is not None and decision.risk_level != "EMERGENCY")

        except ValueError as ve:
            if os.path.exists(audio_file_path):
                try: os.remove(audio_file_path)
                except Exception: pass
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
        except Exception as e:
            logger.error(f"[CryService] Lỗi thực thi Pipeline: {e}")
            if os.path.exists(audio_file_path):
                try: os.remove(audio_file_path)
                except Exception: pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi phân tích tiếng khóc Closed-Loop: {str(e)}"
            )

        now = datetime.now(timezone.utc).isoformat()
        log_obj = CryLogResponse(
            logged_at=now,
            audio_url=audio_url,
            prediction=prediction,
            confidence=confidence,
            reason_scores=reason_scores,
            audio_evidence=audio_evidence,
            context=context_bundle,
            decision=decision,
            advice=advice_text,
            feedback_accurate=None,
            sound_conditioned=sound_conditioned,
            sound_played=sound_played,
            notes=f"Tệp âm thanh tải lên: {safe_filename}"
        )
        return repo.create(log_obj)

    def get_cry_history(self, baby_id: str, user_id: str) -> list[CryLogResponse]:
        """
        Lấy danh sách lịch sử ghi nhận tiếng khóc của bé.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = CryRepository(baby_id)
        logs = repo.list(limit=500)
        logs.sort(key=lambda x: x.logged_at, reverse=True)
        return logs

    def update_parent_feedback(
        self,
        baby_id: str,
        log_id: str,
        feedback: Union[bool, CryFeedbackUpdate, dict],
        user_id: str
    ) -> CryLogResponse:
        """
        Cập nhật phản hồi từ phụ huynh và kết quả can thiệp thực tế (Outcome-Aware Feedback).
        Tương thích ngược cả boolean đơn thuần lẫn payload chi tiết.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = CryRepository(baby_id)
        
        log = repo.get(log_id)
        if not log:
            raise EntityNotFoundError("Không tìm thấy bản ghi tiếng khóc")

        if isinstance(feedback, bool):
            updated_data = {"feedback_accurate": feedback}
        elif isinstance(feedback, CryFeedbackUpdate):
            updated_data = {
                "feedback_accurate": feedback.feedback_accurate,
                "feedback_details": feedback.model_dump()
            }
        elif isinstance(feedback, dict):
            updated_data = {
                "feedback_accurate": feedback.get("feedback_accurate"),
                "feedback_details": feedback
            }
        else:
            updated_data = {"feedback_accurate": bool(feedback)}

        updated_log = repo.update(log_id, updated_data)
        if not updated_log:
            raise EntityNotFoundError("Cập nhật phản hồi thất bại")
        return updated_log

    def delete_cry_log(self, baby_id: str, log_id: str, user_id: str) -> bool:
        """
        Xóa bản ghi lịch sử tiếng khóc.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = CryRepository(baby_id)
        log = repo.get(log_id)
        if not log:
            raise EntityNotFoundError("Không tìm thấy bản ghi tiếng khóc")
        return repo.delete(log_id)
