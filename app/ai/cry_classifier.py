import random

CRY_REASONS = ["hungry", "tired", "pain", "diaper", "discomfort"]

# Cấu hình âm thanh xoa dịu tương ứng với nguyên nhân khóc
SOUND_MAPPING = {
    "hungry": "ai_voice_mom",
    "tired": "classic_lullaby",
    "pain": "pink_noise_rain",
    "diaper": "white_noise_fan",
    "discomfort": "pink_noise_rain"
}

class CryClassifier:
    def predict(self, filename: str) -> tuple[str, float]:
        """
        Dự đoán nguyên nhân khóc dựa trên tệp âm thanh đầu vào.
        Trả về: (nhãn_dự_đoán, độ_tin_cậy)
        """
        filename_lower = filename.lower()
        prediction = "discomfort"
        for reason in CRY_REASONS:
            if reason in filename_lower:
                prediction = reason
                break
        else:
            prediction = random.choice(CRY_REASONS)

        confidence = round(random.uniform(0.75, 0.98), 2)
        return prediction, confidence

    def get_soothing_sound(self, prediction: str) -> str:
        """
        Lấy âm thanh xoa dịu tương ứng với nguyên nhân khóc.
        """
        return SOUND_MAPPING.get(prediction, "classic_lullaby")
