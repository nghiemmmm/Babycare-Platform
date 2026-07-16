"""
Cry Classifier Module
=====================
Phân loại nguyên nhân tiếng khóc của bé từ file âm thanh.

Hiện tại sử dụng rule-based + random để giả lập ML model.
Trong production, thay thế bằng model TensorFlow/PyTorch
hoặc gọi Gemini Multimodal API với audio input.
"""
import random
from app.ai.cry_detection.sound_mapper import CRY_REASONS, SOUND_MAPPING


class CryClassifier:
    """
    Model nhận diện nguyên nhân tiếng khóc của trẻ sơ sinh.
    """

    def predict(self, filename: str) -> tuple[str, float]:
        """
        Dự đoán nguyên nhân khóc từ tên/đường dẫn file âm thanh.

        Args:
            filename: Đường dẫn file audio (.wav, .mp3, v.v.)

        Returns:
            Tuple (nhãn_dự_đoán, độ_tin_cậy)
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

        Args:
            prediction: Nhãn nguyên nhân ("hungry", "tired", v.v.)

        Returns:
            Tên track âm thanh hoặc URL tài nguyên âm thanh.
        """
        return SOUND_MAPPING.get(prediction, "classic_lullaby")
