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

SOUND_MAPPING = {
    "hungry":      "/static/voices/mom/ai_voice_mom.mp3",
    "tired":       "/static/sounds/lullabies/classic_lullaby.mp3",
    "pain":        "/static/sounds/white_noise/pink_noise_rain.mp3",
    "discomfort":  "/static/sounds/white_noise/pink_noise_rain.mp3",
    "burp":        "/static/sounds/lullabies/classic_lullaby.mp3",
    "lonely":      "/static/voices/mom/ai_voice_mom.mp3",
    "scared":      "/static/sounds/white_noise/white_noise_fan.mp3",
    "cold_hot":    "/static/voices/mom/ai_voice_mom.mp3",
    "unknown":     "/static/sounds/white_noise/white_noise_fan.mp3"
}
