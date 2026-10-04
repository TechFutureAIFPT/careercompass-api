from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class AcademicRecord(BaseModel):
    target_block: str = Field(..., description="Tổ hợp xét tuyển mục tiêu: A00, A01, B00, C00, D01, D07, etc.")
    
    # 1. Điểm học bạ THPT (High School Transcript Records)
    gpa_10: Optional[float] = Field(None, ge=0.0, le=10.0, description="Điểm trung bình học bạ lớp 10")
    gpa_11: Optional[float] = Field(None, ge=0.0, le=10.0, description="Điểm trung bình học bạ lớp 11")
    gpa_12: Optional[float] = Field(None, ge=0.0, le=10.0, description="Điểm trung bình học bạ lớp 12 (kỳ 1 hoặc cả năm)")
    transcript_gpa_overall: Optional[float] = Field(None, ge=0.0, le=10.0, description="Điểm trung bình học bạ cả 3 năm THPT (thang 10)")
    transcript_block_score: Optional[float] = Field(None, ge=0.0, le=30.0, description="Tổng điểm học bạ 3 môn theo tổ hợp xét tuyển (thang 30)")
    transcript_subject_scores: Optional[Dict[str, float]] = Field(default_factory=dict, description="Chi tiết điểm học bạ từng môn trong tổ hợp: {'Toán': 8.8, 'Lý': 8.5, 'Hóa': 8.2...}")
    academic_ranking: Optional[str] = Field("Giỏi", description="Xếp loại học lực THPT: Xuất sắc, Giỏi, Khá")
    conduct_ranking: Optional[str] = Field("Tốt", description="Xếp loại hạnh kiểm THPT: Tốt, Khá")

    # 2. Điểm thi tốt nghiệp THPT & Kỳ thi chuẩn hóa
    estimated_exam_score: float = Field(..., ge=0.0, le=30.0, description="Điểm thi tốt nghiệp THPT dự kiến hoặc điểm thi thử (thang 30)")
    favorite_subjects: List[str] = Field(default_factory=list, description="Danh sách môn học yêu thích nhất")
    english_certificate: Optional[str] = Field(None, description="Chứng chỉ tiếng Anh (IELTS, TOEFL, VSTEP)")
    english_score: Optional[float] = Field(None, description="Điểm số chứng chỉ ngoại ngữ (vd: 6.5, 7.0)")
    aptitude_test_type: Optional[str] = Field(None, description="Kỳ thi ĐGNL/ĐGTD (HSA, APT, TSA)")
    aptitude_score: Optional[float] = Field(None, description="Điểm bài thi ĐGNL/ĐGTD")


class QualitativeAnswers(BaseModel):
    strengths: str = Field("", description="Điểm mạnh nổi bật nhất của em")
    weaknesses_to_improve: str = Field("", description="Kỹ năng em muốn cải thiện")
    passionate_interests: str = Field("", description="Sở thích say mê nhất khi rảnh rỗi")
    dream_career: str = Field("", description="Nghề nghiệp em đang mơ ước hoặc cân nhắc")
    parent_wishes: str = Field("", description="Kỳ vọng hoặc định hướng của cha mẹ")
    preferred_region: str = Field("Tất cả", description="Khu vực muốn học tập: Miền Bắc, Miền Trung, Miền Nam, Toàn quốc")
    budget_level: str = Field("Phù hợp", description="Mức học phí mong muốn: Tiêu chuẩn, Vừa phải, Tư thục/Quốc tế")

class SurveySubmission(BaseModel):
    student_name: str = Field(..., min_length=2, description="Họ và tên học sinh")
    school_name: Optional[str] = Field("", description="Trường THPT đang theo học")
    holland_answers: Dict[str, int] = Field(..., description="Map question ID -> rating 1 to 5")
    scct_answers: Dict[str, int] = Field(..., description="Map question ID -> confidence 1 to 5")
    gardner_answers: Dict[str, int] = Field(..., description="Map question ID -> rating 1 to 5")
    disc_answers: Dict[str, int] = Field(..., description="Map question ID -> rating 1 to 5")
    academic: AcademicRecord
    qualitative: QualitativeAnswers
