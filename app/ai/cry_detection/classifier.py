"""
Cry Classifier Module
=====================
Phân loại nguyên nhân tiếng khóc của bé từ file âm thanh sử dụng Audio Spectrogram Transformer (AST).
"""
import os
import tempfile
import logging
import torchaudio
from app.ai.cry_detection.sound_mapper import AST_LABEL_MAPPING, SOUND_MAPPING

logger = logging.getLogger(__name__)


def ensure_wav_format(audio_path: str) -> tuple[str, bool]:
    """
    Kiểm tra nếu file không phải là .wav (ví dụ .mp3, .ogg, .m4a), tự động chuyển đổi sang .wav tạm thời.
    Trả về (wav_path, is_temporary).
    """
    if audio_path.lower().endswith(".wav"):
        return audio_path, False

    try:
        import soundfile as sf
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_wav_path = temp_file.name
        temp_file.close()

        try:
            data, sr = sf.read(audio_path)
            sf.write(temp_wav_path, data, sr, format='WAV', subtype='PCM_16')
            return temp_wav_path, True
        except Exception:
            waveform, sr = torchaudio.load(audio_path)
            torchaudio.save(temp_wav_path, waveform, sr)
            return temp_wav_path, True
    except Exception as e:
        logger.warning(f"Chuyển đổi file âm thanh sang .wav thất bại: {e}")
        return audio_path, False


class CryClassifier:
    """
    Model nhận diện nguyên nhân tiếng khóc của trẻ sơ sinh bằng AST PyTorch Model.
    """

    def predict(self, filename: str) -> tuple[str, float, dict[str, float]]:
        """
        Dự đoán nguyên nhân khóc từ tên/đường dẫn file âm thanh bằng mô hình AST.

        Args:
            filename: Đường dẫn file audio (.wav, .mp3, v.v.)

        Returns:
            Tuple (nhãn_dự_đoán, độ_tin_cậy, bảng_điểm_tất_cả_nguyên_nhân)

        Raises:
            FileNotFoundError: Nếu tệp âm thanh không tồn tại.
            RuntimeError: Nếu suy luận mô hình AST gặp lỗi.
        """
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Tệp âm thanh không tồn tại: {filename}")

        wav_path = filename
        is_temp = False
        try:
            wav_path, is_temp = ensure_wav_format(filename)
            from app.ai.CRY.inference import inference
            res = inference(wav_path)
            raw_label = res.get("label", "dc")
            confidence = float(res.get("confidence", 0.0))
            prediction = AST_LABEL_MAPPING.get(raw_label, "discomfort")

            raw_scores = res.get("scores", {})
            reason_scores = {}
            for code, score in raw_scores.items():
                mapped_name = AST_LABEL_MAPPING.get(code, code)
                score_val = round(float(score), 4)
                if mapped_name in reason_scores:
                    reason_scores[mapped_name] = max(reason_scores[mapped_name], score_val)
                else:
                    reason_scores[mapped_name] = score_val

            sorted_reason_scores = dict(sorted(reason_scores.items(), key=lambda x: x[1], reverse=True))
            return prediction, confidence, sorted_reason_scores
        except Exception as e:
            logger.error(f"Lỗi suy luận AST mô hình tiếng khóc trên file {filename}: {e}")
            err_msg = str(e).lower()
            if any(k in err_msg for k in ["audio", "soundfile", "format", "header", "decode", "backend"]):
                raise ValueError("Tệp âm thanh không hợp lệ hoặc bị lỗi định dạng audio (không thể giải mã).") from e
            raise RuntimeError(f"Lỗi phân loại tiếng khóc bằng AST model: {str(e)}") from e
        finally:
            if is_temp and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except Exception:
                    pass

    def get_soothing_sound(self, prediction: str) -> str:
        """
        Lấy âm thanh xoa dịu tương ứng với nguyên nhân khóc.

        Args:
            prediction: Nhãn nguyên nhân ("hungry", "tired", v.v.)

        Returns:
            Tên track âm thanh hoặc URL tài nguyên âm thanh.
        """
        return SOUND_MAPPING.get(prediction, "classic_lullaby")


