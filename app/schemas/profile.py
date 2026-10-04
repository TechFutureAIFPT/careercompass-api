from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.survey import AcademicRecord, QualitativeAnswers

class HollandScoreResult(BaseModel):
    scores: Dict[str, float] = Field(..., description="Điểm thô của 6 nhóm R, I, A, S, E, C")
    percentages: Dict[str, float] = Field(..., description="Tỷ lệ % chuẩn hóa của 6 nhóm")
    holland_code: str = Field(..., description="Mật mã Holland 3 chữ cái, ví dụ: IRE, SEC")
    primary_trait: str = Field(..., description="Đặc điểm tính cách nghề nghiệp chủ đạo")

class SCCTQuadrantItem(BaseModel):
    group: str
    dimension_name: str
    interest_score: float
    confidence_score: float
    quadrant: str = Field(..., description="Hành động (Action), Rèn luyện (Develop), Dự phòng (Backup), Hạn chế (Avoid)")
    advice: str

class GardnerScoreResult(BaseModel):
    scores: Dict[str, float] = Field(..., description="Điểm số 8 loại trí thông minh")
    top_intelligences: List[str] = Field(..., description="Top 3 loại trí thông minh vượt trội")
    learning_style_advice: str

class DISCScoreResult(BaseModel):
    scores: Dict[str, float] = Field(..., description="Điểm 4 nhóm D, I, S, C")
    dominant_trait: str = Field(..., description="Phong cách chủ đạo (D, I, S, C)")
    workplace_style: str = Field(..., description="Môi trường làm việc và vai trò nhóm phù hợp")

class MajorMatchResult(BaseModel):
    code: str
    name: str
    match_score: float = Field(..., description="Tỷ lệ phù hợp (0 - 100%)")
    holland_code: str
    popular_careers: List[str]
    salary_range: str
    growth_outlook: str
    suitable_reason: str

class StudentCareerProfile(BaseModel):
    id: str
    created_at: str
    student_name: str
    school_name: Optional[str] = ""
    academic: AcademicRecord
    qualitative: QualitativeAnswers
    holland: HollandScoreResult
    scct: List[SCCTQuadrantItem]
    gardner: GardnerScoreResult
    disc: DISCScoreResult
    top_majors: List[MajorMatchResult]
    ai_executive_summary: str = Field(..., description="Lời tư vấn tổng hợp từ Hệ thống Cố vấn Hướng nghiệp AI")
