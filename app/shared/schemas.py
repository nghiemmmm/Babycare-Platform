from pydantic import BaseModel
from typing import Optional

class Message(BaseModel):
    """
    Đại diện cho một phản hồi chứa thông điệp (message) chung từ API.
    """
    message: str


class AsyncJobCreatedResponse(BaseModel):
    """
    Phản hồi khi một tác vụ xử lý nền (Async Job) được khởi tạo thành công (HTTP 202 Accepted).
    """
    job_id: str
    status: str = "PENDING"
    message: str = "Nhắc nhở theo dõi sức khỏe cho bé đang được khởi tạo..."
