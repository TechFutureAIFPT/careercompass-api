from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class RAGChunkItem(BaseModel):
    id: str
    title: str
    category: str
    content: str
    source: str
    relevance_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Nội dung truy vấn quy chế, điểm chuẩn hoặc định hướng")
    top_k: int = Field(5, ge=1, le=20, description="Số lượng phân đoạn tài liệu trả về")
    category_filter: Optional[str] = Field(None, description="Lọc danh mục: regulations_2026, cutoff_benchmarks, major_profiles, holland_assessment, university_scheme")

class RAGRetrieveResponse(BaseModel):
    query: str
    total_found: int
    chunks: List[RAGChunkItem]

class RAGAskRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Câu hỏi tuyển sinh cần AI tra cứu và trả lời có kiểm chứng")
    top_k: int = Field(4, ge=1, le=10, description="Số lượng tài liệu viện dẫn")

class RAGAskResponse(BaseModel):
    query: str
    answer: str
    grounded_context_summary: str
    citations: List[Dict[str, Any]]
    related_document_ids: List[str]

class RAGDocumentSummary(BaseModel):
    id: str
    title: str
    category: str
    source: str
    token_count: int
