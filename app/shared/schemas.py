from pydantic import BaseModel

class Message(BaseModel):
    """
    Đại diện cho một phản hồi chứa thông điệp (message) chung từ API.
    """
    message: str
