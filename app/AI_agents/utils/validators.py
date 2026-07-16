from typing import Optional

def validate_baby_id(baby_id: Optional[str]) -> bool:
    """Return True if baby_id is a non-empty string."""
    return bool(baby_id and baby_id.strip())


def validate_audio_file(file_path: Optional[str]) -> bool:
    """Return True if the file path ends with a supported audio extension."""
    if not file_path:
        return False
    return file_path.lower().endswith((".wav", ".mp3", ".ogg", ".m4a", ".flac"))


def validate_message_not_empty(message: Optional[str]) -> bool:
    """Return True if message is not None or blank."""
    return bool(message and message.strip())
