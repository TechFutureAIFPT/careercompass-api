from typing import List, Optional
from pydantic import BaseModel, Field

class UniversityRecommendationItem(BaseModel):
    university_id: str
    university_name: str
    university_code: str
    major_code: str
    major_name: str
    field_code: str
    region: str
    location: str
    exam_block: str
    benchmark_2024: float
    benchmark_2025: float
    benchmark_pred_2026: float
    student_score: float
    score_delta: float = Field(..., description="Chênh lệch điểm = Điểm học sinh - Điểm chuẩn dự kiến")
    tier: str = Field(..., description="Mơ ước (Dream), Vừa sức (Target), An toàn (Safety)")
    tuition_range: str
    admission_methods: List[str]
    ielts_policy: str
    official_website: str
    verification_source: str
    match_reason: str

class RecommendationResponse(BaseModel):
    student_name: str
    target_block: str
    estimated_score: float
    dream_tier: List[UniversityRecommendationItem] = Field(..., description="Nhóm nguyện vọng Mơ ước (+0.5 đến +2.0 điểm)")
    target_tier: List[UniversityRecommendationItem] = Field(..., description="Nhóm nguyện vọng Vừa sức (tiệm cận ±0.5 điểm)")
    safety_tier: List[UniversityRecommendationItem] = Field(..., description="Nhóm nguyện vọng An toàn (dư từ 1.5 - 3.0 điểm)")
    strategic_advice: str

class ComparisonRequest(BaseModel):
    selected_options: List[dict] = Field(..., description="Danh sách các cặp trường - ngành cần so sánh đa tiêu chí")
