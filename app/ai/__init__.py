"""
app/ai - Phân hệ AI chuyên biệt của BabyCare

Bao gồm 3 module nhận dạng/tổng hợp âm thanh:
- cry_detection: Nhận diện nguyên nhân tiếng khóc của bé
- speech_to_text: Chuyển đổi giọng nói phụ huynh thành văn bản
- voice_clone: Tổng hợp và nhân bản giọng nói (Voice Cloning / TTS)
"""
from app.ai.cry_detection import CryClassifier
from app.ai.speech_to_text import SpeechTranscriber
from app.ai.voice_clone import VoiceSynthesizer
