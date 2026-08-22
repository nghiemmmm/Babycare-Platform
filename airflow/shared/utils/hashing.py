import hashlib
import os
from typing import BinaryIO, Union


def compute_file_sha256(file_input: Union[str, BinaryIO], chunk_size: int = 65536) -> str:
    """
    Tính mã băm SHA-256 của tập tin (từ đường dẫn file hoặc stream nhị phân).

    Args:
        file_input: Đường dẫn chuỗi đến file hoặc đối tượng file nhị phân mở (file-like object).
        chunk_size: Kích thước từng khối đọc vào bộ nhớ (mặc định 64KB).

    Returns:
        Chuỗi hex biểu diễn mã SHA-256.
    """
    sha256_hash = hashlib.sha256()

    if isinstance(file_input, str):
        if not os.path.exists(file_input):
            raise FileNotFoundError(f"Tập tin không tồn tại: {file_input}")
        with open(file_input, "rb") as f:
            for byte_block in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(byte_block)
    else:
        curr_pos = 0
        if hasattr(file_input, "tell"):
            try:
                curr_pos = file_input.tell()
            except Exception:
                pass
        
        for byte_block in iter(lambda: file_input.read(chunk_size), b""):
            sha256_hash.update(byte_block)
            
        if hasattr(file_input, "seek"):
            try:
                file_input.seek(curr_pos)
            except Exception:
                pass

    return sha256_hash.hexdigest()


def compute_text_sha256(text: str) -> str:
    """
    Tính mã băm SHA-256 cho chuỗi văn bản UTF-8 (dùng cho deduplication của Chunks).

    Args:
        text: Chuỗi văn bản cần tính băm.

    Returns:
        Chuỗi hex biểu diễn mã SHA-256.
    """
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


# Alias helpers matching PyImageSearch conventions
hash_file = compute_file_sha256
hash_content = compute_text_sha256
