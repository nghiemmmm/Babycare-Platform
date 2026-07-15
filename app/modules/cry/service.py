"""
AI Cry Tracking & Prediction Service Module

Handles business logic and delegates AI classification to CryClassifier.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import UploadFile
from app.modules.cry.schemas import CryLogCreate, CryLogResponse
from app.modules.cry.repository import CryRepository
from app.modules.baby.service import BabyService
from app.ai import CryClassifier
from app.shared.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)

class CryService:
    def __init__(self, baby_service: Optional[BabyService] = None):
        self.baby_service = baby_service or BabyService()

    def predict_cry(self, baby_id: str, audio_file: UploadFile, user_id: str) -> CryLogResponse:
        """
        Nhận tệp ghi âm tiếng khóc, thực hiện chẩn đoán AI bằng CryClassifier,
        tự động kích hoạt âm thanh dỗ bé và lưu kết quả vào Firestore.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = CryRepository(baby_id)

        # Giả lập tải tệp ghi âm lên Firebase Storage (trả về URL giả định)
        safe_filename = audio_file.filename.replace(" ", "_")
        dummy_audio_url = f"https://storage.googleapis.com/babycare-ai-cries/{baby_id}/{safe_filename}"

        # Ủy quyền chẩn đoán AI cho lớp CryClassifier dùng chung
        classifier = CryClassifier()
        prediction, confidence = classifier.predict(safe_filename)
        
        sound_conditioned = True
        sound_played = classifier.get_soothing_sound(prediction)

        now = datetime.now(timezone.utc).isoformat()
        log_obj = CryLogResponse(
            logged_at=now,
            audio_url=dummy_audio_url,
            prediction=prediction,
            confidence=confidence,
            feedback_accurate=None,
            sound_conditioned=sound_conditioned,
            sound_played=sound_played,
            notes=f"Tệp âm thanh tải lên: {audio_file.filename}"
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

    def update_parent_feedback(self, baby_id: str, log_id: str, feedback_accurate: bool, user_id: str) -> CryLogResponse:
        """
        Cập nhật phản hồi từ phụ huynh để đánh giá độ chính xác của AI.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = CryRepository(baby_id)
        
        log = repo.get(log_id)
        if not log:
            raise EntityNotFoundError("Không tìm thấy bản ghi tiếng khóc")
            
        updated_data = {"feedback_accurate": feedback_accurate}
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
