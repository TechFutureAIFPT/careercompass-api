from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class UserProfileRequest(BaseModel):
    id: Optional[str] = Field(None, description="Supabase Auth UUID hoặc định danh duy nhất")
    email: Optional[str] = Field(None, description="Địa chỉ email của học sinh")
    full_name: str = Field(..., description="Họ và tên học sinh")
    phone_number: Optional[str] = Field(None, description="Số điện thoại liên hệ")
    school_name: Optional[str] = Field(None, description="Trường THPT đang theo học")
    province: Optional[str] = Field(None, description="Tỉnh/Thành phố")
    grade: int = Field(12, description="Khối lớp (mặc định 12)")
    target_block: str = Field("A00", description="Khối thi mục tiêu chính (A00, A01, D01,...)")

class UserProfileResponse(BaseModel):
    id: str
    email: Optional[str] = None
    full_name: str
    phone_number: Optional[str] = None
    school_name: Optional[str] = None
    province: Optional[str] = None
    grade: int = 12
    target_block: str = "A00"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class AcademicRecordSaveRequest(BaseModel):
    user_id: str = Field(..., description="UUID của học sinh")
    target_block: str = Field("A00", description="Khối thi đại học")
    favorite_subjects: List[str] = Field(default_factory=list, description="Danh sách các môn học yêu thích")
    estimated_exam_score: float = Field(..., description="Điểm thi tốt nghiệp THPT dự kiến (thang 30)")
    
    # Học bạ THPT chi tiết
    gpa_10: Optional[float] = Field(None, description="Điểm trung bình năm lớp 10")
    gpa_11: Optional[float] = Field(None, description="Điểm trung bình năm lớp 11")
    gpa_12: Optional[float] = Field(None, description="Điểm trung bình học kỳ/cả năm lớp 12")
    transcript_gpa_overall: Optional[float] = Field(None, description="Điểm trung bình chung học bạ 3 năm THPT")
    transcript_block_score: Optional[float] = Field(None, description="Tổng điểm học bạ tổ hợp 3 môn xét tuyển")
    academic_ranking: Optional[str] = Field("Giỏi", description="Xếp loại học lực (Xuất sắc, Giỏi, Khá, Trung bình)")
    conduct_ranking: Optional[str] = Field("Tốt", description="Hạnh kiểm (Tốt, Khá)")
    english_certificate_type: Optional[str] = Field(None, description="Loại chứng chỉ ngoại ngữ (IELTS, TOEFL, TOEIC)")
    english_certificate_score: Optional[float] = Field(None, description="Điểm số chứng chỉ (ví dụ: 6.5, 7.0)")
    priority_area: Optional[str] = Field("KV3", description="Khu vực ưu tiên (KV1, KV2-NT, KV2, KV3)")
    priority_object: Optional[str] = Field(None, description="Đối tượng ưu tiên (01, 02,...)")

class BookmarkToggleRequest(BaseModel):
    user_id: str = Field(..., description="UUID của học sinh")
    university_code: str = Field(..., description="Mã trường đại học (ví dụ: BKA, NEU, QHI)")
    major_code: str = Field(..., description="Mã ngành đào tạo (ví dụ: 7480201)")
    university_name: Optional[str] = Field("", description="Tên trường")
    major_name: Optional[str] = Field("", description="Tên ngành")
    cutoff_score_2025: Optional[float] = Field(25.0, description="Điểm chuẩn tham chiếu")

class WishlistItemResponse(BaseModel):
    id: str
    user_id: str
    university_code: str
    major_code: str
    university_name: str
    major_name: str
    cutoff_score_2025: float
    created_at: str

class UserDashboardSummaryResponse(BaseModel):
    user: Optional[UserProfileResponse] = None
    academic_record: Optional[Dict[str, Any]] = None
    career_profile_id: Optional[str] = None
    holland_code: Optional[str] = None
    wishlist_count: int = 0
    wishlist_items: List[WishlistItemResponse] = Field(default_factory=list)
    total_surveys_completed: int = 0
