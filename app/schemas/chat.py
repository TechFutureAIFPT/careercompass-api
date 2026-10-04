from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message text")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Nội dung câu hỏi của học sinh")
    conversation_history: List[ChatMessage] = Field(default_factory=list, description="Lịch sử đối thoại trước đó")
    student_profile_context: Optional[Dict[str, Any]] = Field(None, description="Hồ sơ cá nhân của học sinh nếu đã làm khảo sát")
    use_deep_research: bool = Field(True, description="Kích hoạt tra cứu thời gian thực dữ liệu Bộ GD&ĐT")
    user_id: Optional[str] = Field(None, description="ID học sinh để lưu lịch sử cuộc trò chuyện")
    conversation_id: Optional[str] = Field(None, description="ID phiên hội thoại")

class CitationItem(BaseModel):
    source_title: str
    source_url: str
    tier: str = Field(..., description="Cấp 1 (Bộ GD&ĐT), Cấp 2 (Tổ chức QT), Cấp 3 (Tuyển dụng/Trường), Cấp 4 (Báo chí)")
    verified: bool = True

class ChatResponse(BaseModel):
    reply: str = Field(..., description="Câu trả lời tư vấn hoàn chỉnh từ AI")
    thought_process: Optional[str] = Field(None, description="Chuỗi suy luận (Chain-of-Thought) của DeepSeek")
    citations: List[CitationItem] = Field(default_factory=list, description="Danh mục nguồn trích dẫn pháp lý và tuyển sinh minh bạch")
    recommended_followups: List[str] = Field(default_factory=list, description="Gợi ý câu hỏi đào sâu tiếp theo")
    conversation_id: Optional[str] = Field(None, description="ID phiên hội thoại")
