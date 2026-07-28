CRY_REASONS = ["hungry", "tired", "pain", "diaper", "discomfort", "burp", "lonely", "scared"]

AST_LABEL_MAPPING = {
    "bp": "pain",        # Belly Pain
    "bu": "burp",        # Burp
    "ch": "discomfort",  # Cold/Hot
    "dc": "discomfort",  # Discomfort
    "dk": "diaper",      # Diaper/Colic
    "hu": "hungry",      # Hungry
    "lo": "lonely",      # Lonely
    "sc": "scared",      # Scared
    "ti": "tired"        # Tired
}

SOUND_MAPPING = {
    "hungry":      "/static/voices/mom/ai_voice_mom.mp3",
    "tired":       "/static/sounds/lullabies/classic_lullaby.mp3",
    "pain":        "/static/sounds/white_noise/pink_noise_rain.mp3",
    "diaper":      "/static/sounds/white_noise/white_noise_fan.mp3",
    "discomfort":  "/static/sounds/white_noise/pink_noise_rain.mp3",
    "burp":        "/static/sounds/lullabies/classic_lullaby.mp3",
    "lonely":      "/static/voices/mom/ai_voice_mom.mp3",
    "scared":      "/static/sounds/white_noise/white_noise_fan.mp3"
}

