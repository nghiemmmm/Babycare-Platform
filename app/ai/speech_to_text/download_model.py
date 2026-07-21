import os
import sys

# Đảm bảo đường dẫn của project nằm trong python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from faster_whisper import WhisperModel
from app.core.config import settings

def main():
    print(f"==================================================")
    print(f"Downloading Faster-Whisper Model from Hugging Face")
    print(f"==================================================")
    print(f"Model size:  {settings.WHISPER_MODEL_SIZE}")
    print(f"Save path:   {settings.WHISPER_MODEL_DIR}")
    
    os.makedirs(settings.WHISPER_MODEL_DIR, exist_ok=True)
    
    try:
        # Tải mô hình sử dụng CPU/float32 để lưu cache ngoại tuyến
        model = WhisperModel(
            settings.WHISPER_MODEL_SIZE,
            device="cpu",
            compute_type="float32",
            download_root=settings.WHISPER_MODEL_DIR
        )
        print("--------------------------------------------------")
        print("Success: Faster-Whisper model downloaded successfully!")
        print(f"Location: {os.path.abspath(settings.WHISPER_MODEL_DIR)}")
        print("==================================================")
    except Exception as e:
        print(f"Error downloading model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
