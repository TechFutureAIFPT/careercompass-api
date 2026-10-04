from typing import List, Optional
from pydantic import BaseModel, Field

class MajorInfo(BaseModel):
    code: str
    name: str
    block: str
    score_2024: float
    score_2025: float
    score_pred_2026: float
    field_code: str

class UniversityDetail(BaseModel):
    id: str
    code: str
    name: str
    english_name: str
    region: str
    location: str
    type: str
    tuition_range: str
    tuition_number: float
    quota_2026: int
    admission_methods: List[str]
    ielts_policy: str
    website: str
    verification_source: str
    last_updated: str
    majors: List[MajorInfo]

class UniversityFilterParams(BaseModel):
    keyword: Optional[str] = None
    region: Optional[str] = None
    field_code: Optional[str] = None
    max_tuition: Optional[float] = None
    exam_block: Optional[str] = None
    min_score: Optional[float] = None
    max_score: Optional[float] = None
