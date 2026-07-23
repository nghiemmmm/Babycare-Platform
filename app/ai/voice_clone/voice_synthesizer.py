"""
Voice Synthesizer Module (Voice Cloning)
==========================================
Giả lập giọng nói của mẹ để dỗ trẻ sơ sinh.

Trong production, tích hợp với:
- ElevenLabs Voice Cloning API
- OpenAI TTS API
- Google Cloud Text-to-Speech

Hiện tại sử dụng Gemini TTS hoặc trả về URL tĩnh làm placeholder.
"""
from typing import Optional
from app.core.config import settings


VOICE_PROFILES = {
    "default_mom": "calm_female_vn",
    "soft_lullaby": "soft_lullaby_vn",
    "soothing_whisper": "whisper_female_vn"
}


class VoiceSynthesizer:
    """
    Model tổng hợp và nhân bản giọng nói (Voice Cloning / TTS).
    """

    def __init__(self, voice_profile: str = "default_mom"):
        self.voice_profile = VOICE_PROFILES.get(voice_profile, "calm_female_vn")

    def synthesize(self, text: str, output_path: Optional[str] = None) -> dict:
        """
        Tổng hợp giọng nói từ văn bản.

        Args:
            text: Văn bản cần đọc (lời dỗ bé, câu hát ru)
            output_path: Đường dẫn lưu file audio (nếu cần)

        Returns:
            Dict chứa `audio_url` hoặc `audio_data` (base64).
        """
        # Placeholder: trong production kết nối ElevenLabs hoặc Google TTS
        return {
            "voice_profile": self.voice_profile,
            "text": text,
            "audio_url": f"/static/voices/mom/{self.voice_profile}_tts.mp3",
            "status": "simulated"
        }

    def get_lullaby_audio(self, reason: str) -> dict:
        """
        Lấy bài hát ru hoặc âm thanh xoa dịu phù hợp theo nguyên nhân khóc.

        Args:
            reason: Nguyên nhân khóc ("hungry", "tired", "pain", v.v.)

        Returns:
            Dict chứa `audio_url` của bài hát ru.
        """
        LULLABY_TRACKS = {
            "hungry":     "ru_con_dem_dong.mp3",
            "tired":      "ba_thang_bong_bong.mp3",
            "pain":       "pink_noise_ocean.mp3",
            "diaper":     "white_noise_fan.mp3",
            "discomfort": "pink_noise_rain.mp3"
        }
        track = LULLABY_TRACKS.get(reason, "classic_lullaby.mp3")
        return {
            "track": track,
            "audio_url": f"/static/sounds/lullabies/{track}",
            "reason": reason
        }
