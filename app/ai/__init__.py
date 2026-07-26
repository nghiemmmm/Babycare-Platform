"""
app/ai - Phân hệ AI chuyên biệt của BabyCare

Bao gồm 2 module nhận dạng/tổng hợp âm thanh:
- cry_detection: Nhận diện nguyên nhân tiếng khóc của bé bằng AST PyTorch Model
- voice_clone: Tổng hợp và nhân bản giọng nói (Voice Cloning / TTS)

Ghi chú: Chức năng Speech-to-Text (STT) đã được chuyển sang thực hiện ở phía Giao diện (Frontend).
"""
from app.ai.cry_detection import CryClassifier
from app.ai.voice_clone import VoiceSynthesizer

__all__ = ["CryClassifier", "VoiceSynthesizer"]

