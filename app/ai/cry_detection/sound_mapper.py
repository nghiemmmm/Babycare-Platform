CRY_REASONS = ["hungry", "burp", "pain", "discomfort", "tired", "lonely", "cold_hot", "scared", "unknown"]

AST_LABEL_MAPPING = {
    "hu": "hungry",      # Hungry (Đói)
    "bu": "burp",        # Needs burping (Cần ợ hơi)
    "bp": "pain",        # Belly pain (Đau bụng/Đầy hơi)
    "dc": "discomfort",  # Discomfort (Khó chịu)
    "ti": "tired",       # Tired (Mệt mỏi/Gắt ngủ)
    "lo": "lonely",      # Lonely (Cô đơn/Cần bế)
    "ch": "cold_hot",    # Cold/Hot (Nóng/Lạnh)
    "sc": "scared",      # Scared (Giật mình/Sợ hãi)
    "dk": "unknown"      # Don't know (Chưa rõ nguyên nhân)
}

SOUND_MAPPING = {
    "hungry":      "/static/voices/mom/ai_voice_mom.mp3",
    "burp":        "/static/sounds/lullabies/classic_lullaby.mp3",
    "pain":        "/static/sounds/white_noise/pink_noise_rain.mp3",
    "discomfort":  "/static/sounds/white_noise/pink_noise_rain.mp3",
    "tired":       "/static/sounds/lullabies/classic_lullaby.mp3",
    "lonely":      "/static/voices/mom/ai_voice_mom.mp3",
    "cold_hot":    "/static/sounds/white_noise/pink_noise_rain.mp3",
    "scared":      "/static/sounds/white_noise/white_noise_fan.mp3",
    "unknown":     "/static/sounds/white_noise/pink_noise_rain.mp3"
}

