CRY_REASONS = ["hungry", "tired", "pain", "discomfort", "burp", "lonely", "scared", "cold_hot", "unknown"]

AST_LABEL_MAPPING = {
    "hu": "hungry",      # Hungry (Đói)
    "bu": "burp",        # Needs burping (Cần ợ hơi)
    "bp": "pain",        # Belly pain (Đau bụng)
    "dc": "discomfort",  # Discomfort (Khó chịu)
    "ti": "tired",       # Tired (Gắt ngủ)
    "lo": "lonely",      # Lonely (Cần bế)
    "ch": "cold_hot",    # Cold/Hot (Quá nóng hoặc lạnh)
    "sc": "scared",      # Scared (Giật mình hoặc sợ hãi)
    "dk": "unknown"      # Don't know (Chưa rõ nguyên nhân)
}

# Trỏ tới các tệp âm thanh THỰC SỰ có trong app/static/ (được serve qua backend
# /static/, và qua nginx gateway proxy /static/ -> backend). Trước đây map trỏ tới
# các tên .mp3 không tồn tại ở bất kỳ đâu (classic_lullaby.mp3, pink_noise_rain.mp3...)
# nên trình phát luôn 404. Thêm tệp mới vào các thư mục này rồi cập nhật path tương ứng.
SOUND_MAPPING = {
    "hungry":      "/static/voices/mom/ai_voice_mom.wav",
    "tired":       "/static/sounds/lullabies/1.wav",
    "pain":        "/static/sounds/white_noise/1.wav",
    "discomfort":  "/static/sounds/white_noise/1.wav",
    "burp":        "/static/sounds/lullabies/1.wav",
    "lonely":      "/static/voices/mom/ai_voice_mom.wav",
    "scared":      "/static/sounds/white_noise/1.wav",
    "cold_hot":    "/static/voices/mom/ai_voice_mom.wav",
    "unknown":     "/static/sounds/white_noise/1.wav",
}


def get_soothing_sound_url(reason: str) -> str:
    # Trả thẳng đường dẫn /static/ nội bộ. Đây là asset đóng gói sẵn của app, không
    # phải file người dùng upload — phục vụ trực tiếp từ backend ổn định hơn là ép
    # qua Cloudinary (chỉ tồn tại sau khi chạy scripts/sync_static_to_cloudinary.py).
    return SOUND_MAPPING.get(reason, SOUND_MAPPING["unknown"])

