"""
app/ai - Phân hệ AI chuyên biệt của BabyCare

Bao gồm module nhận dạng âm thanh:
- cry_detection: Nhận diện nguyên nhân tiếng khóc của bé bằng AST PyTorch Model
"""
from app.ai.cry_detection import CryClassifier

__all__ = ["CryClassifier"]
