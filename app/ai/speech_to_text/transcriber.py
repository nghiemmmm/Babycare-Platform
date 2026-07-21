"""
Speech-to-Text Transcriber Module
==================================
Chuyển đổi giọng nói của phụ huynh sang văn bản để ghi nhật ký hoạt động bé.

Hiện tại sử dụng Google Gemini Multimodal API với inline audio data.
Trong production có thể thay thế bằng Whisper hoặc Google Cloud Speech-to-Text.
"""
import os
import base64
from typing import Optional
from app.core.config import settings
from app.AI_agents.core.logger import get_agent_logger

logger = get_agent_logger("speech_transcriber")


class SpeechTranscriber:
    """
    Model chuyển đổi giọng nói sang văn bản (Speech-to-Text) hỗ trợ offline qua Faster-Whisper
    hoặc cloud qua Google Gemini API.
    """

    def __init__(self):
        self.provider = settings.STT_PROVIDER
        self.gemini_model_name = "gemini-2.0-flash"
        self._whisper_model = None

    def _get_whisper_model(self):
        """Lazy initialization of Faster-Whisper model with hardware auto-detection."""
        if self._whisper_model is None:
            from faster_whisper import WhisperModel
            
            # Khởi tạo thư mục chứa model nếu chưa tồn tại
            os.makedirs(settings.WHISPER_MODEL_DIR, exist_ok=True)
            
            # Tự động chọn GPU nếu khả dụng, nếu không dùng CPU
            device = "cpu"
            compute_type = "float32"
            
            try:
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
                    compute_type = "float16"
                    logger.info("CUDA is available. Running Whisper on CUDA (float16).")
                else:
                    logger.info("CUDA not found. Running Whisper on CPU (float32).")
            except ImportError:
                logger.info("Torch not installed. Running Whisper on CPU (float32).")

            logger.info(
                f"Loading Faster-Whisper model '{settings.WHISPER_MODEL_SIZE}' "
                f"from Hugging Face to '{settings.WHISPER_MODEL_DIR}'..."
            )
            
            self._whisper_model = WhisperModel(
                settings.WHISPER_MODEL_SIZE,
                device=device,
                compute_type=compute_type,
                download_root=settings.WHISPER_MODEL_DIR
            )
            logger.info("Faster-Whisper model loaded successfully.")
            
        return self._whisper_model

    def transcribe(self, audio_file_path: str) -> Optional[str]:
        """
        Chuyển đổi file âm thanh thành văn bản.

        Args:
            audio_file_path: Đường dẫn file âm thanh (.wav, .mp3, .ogg, .m4a)

        Returns:
            Chuỗi văn bản đã được nhận diện, hoặc None nếu thất bại.
        """
        if not os.path.isfile(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return None

        # Sử dụng Faster-Whisper
        if self.provider == "whisper":
            try:
                model = self._get_whisper_model()
                logger.info(f"Transcribing '{audio_file_path}' using local Faster-Whisper...")
                segments, info = model.transcribe(audio_file_path, beam_size=5)
                # Ghép các đoạn nhận diện lại
                text = " ".join([segment.text for segment in segments])
                return text.strip() if text.strip() else None
            except Exception as e:
                logger.error(f"Faster-Whisper transcription failed: {e}. Falling back to Gemini...")
                # Nếu whisper lỗi, tự động fallback sang Gemini
                return self._transcribe_gemini(audio_file_path)
        else:
            return self._transcribe_gemini(audio_file_path)

    def _transcribe_gemini(self, audio_file_path: str) -> Optional[str]:
        """Phương thức dự phòng sử dụng Gemini API."""
        try:
            logger.info(f"Transcribing '{audio_file_path}' using Gemini API...")
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)

            model = genai.GenerativeModel(self.gemini_model_name)

            with open(audio_file_path, "rb") as f:
                audio_data = f.read()

            audio_b64 = base64.b64encode(audio_data).decode("utf-8")
            ext = os.path.splitext(audio_file_path)[1].lower().lstrip(".")
            mime = f"audio/{ext}" if ext else "audio/wav"

            response = model.generate_content([
                {"mime_type": mime, "data": audio_b64},
                "Hãy chuyển toàn bộ nội dung giọng nói trong đoạn audio này thành văn bản tiếng Việt. Chỉ trả về văn bản, không giải thích gì thêm."
            ])
            return response.text.strip() if response.text else None
        except Exception as e:
            logger.error(f"Gemini API transcription failed: {e}")
            return None

    def transcribe_text(self, text: str) -> str:
        """Passthrough cho văn bản đã nhập sẵn (non-audio path)."""
        return text.strip()

