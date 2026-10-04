from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.services.supabase_service import supabase_service
from app.services.scoring_engine import evaluate_full_survey
from app.schemas.survey import SurveySubmission, AcademicRecord, QualitativeAnswers

router = APIRouter()

@router.get("/{profile_id}", summary="Lấy chi tiết Hồ sơ Hướng nghiệp theo ID")
async def get_profile(profile_id: str) -> Dict[str, Any]:
    profile = await supabase_service.get_student_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ học sinh tương ứng")
    return {"success": True, "data": profile}

@router.get("/demo/sample", summary="Lấy hồ sơ mẫu thực tế của học sinh lớp 12 để trải nghiệm ngay")
async def get_sample_demo_profile() -> Dict[str, Any]:
    sample_sub = SurveySubmission(
        student_name="Nguyễn Hoàng Nam",
        school_name="THPT Chuyên Hà Nội - Amsterdam",
        holland_answers={
            "R1": 4, "R2": 4, "R3": 3, "R4": 5, "R5": 5,
            "I1": 5, "I2": 5, "I3": 5, "I4": 4, "I5": 5,
            "A1": 3, "A2": 4, "A3": 2, "A4": 4, "A5": 3,
            "S1": 3, "S2": 3, "S3": 3, "S4": 2, "S5": 4,
            "E1": 4, "E2": 3, "E3": 4, "E4": 4, "E5": 4,
            "C1": 3, "C2": 4, "C3": 3, "C4": 4, "C5": 3
        },
        scct_answers={
            "SCCT_R1": 4, "SCCT_R2": 5, "SCCT_R3": 4,
            "SCCT_I1": 5, "SCCT_I2": 5, "SCCT_I3": 5,
            "SCCT_A1": 3, "SCCT_A2": 3, "SCCT_A3": 4,
            "SCCT_S1": 3, "SCCT_S2": 4, "SCCT_S3": 3,
            "SCCT_E1": 4, "SCCT_E2": 4, "SCCT_E3": 4,
            "SCCT_C1": 3, "SCCT_C2": 4, "SCCT_C3": 4
        },
        gardner_answers={
            "G_LOG1": 5, "G_LOG2": 5, "G_LOG3": 5,
            "G_SPA1": 4, "G_SPA2": 5, "G_SPA3": 4,
            "G_LING1": 4, "G_LING2": 3, "G_LING3": 4,
            "G_INTRA1": 4, "G_INTRA2": 5, "G_INTRA3": 4,
            "G_INTER1": 3, "G_INTER2": 4, "G_INTER3": 3,
            "G_BOD1": 3, "G_BOD2": 3, "G_BOD3": 4,
            "G_MUS1": 2, "G_MUS2": 3, "G_MUS3": 2,
            "G_NAT1": 3, "G_NAT2": 3, "G_NAT3": 3
        },
        disc_answers={
            "DISC_D1": 4, "DISC_D2": 4, "DISC_D3": 4, "DISC_D4": 4,
            "DISC_I1": 3, "DISC_I2": 3, "DISC_I3": 3, "DISC_I4": 3,
            "DISC_S1": 3, "DISC_S2": 3, "DISC_S3": 4, "DISC_S4": 3,
            "DISC_C1": 5, "DISC_C2": 5, "DISC_C3": 4, "DISC_C4": 5
        },
        academic=AcademicRecord(
            target_block="A00",
            gpa_10=8.8,
            gpa_11=9.1,
            gpa_12=9.2,
            estimated_exam_score=27.5,
            favorite_subjects=["Toán học", "Vật lý", "Tin học"],
            english_certificate="IELTS",
            english_score=7.0,
            aptitude_test_type="TSA (ĐGTD Bách Khoa)",
            aptitude_score=78.5
        ),
        qualitative=QualitativeAnswers(
            strengths="Tư duy thuật toán tốt, kiên trì gỡ lỗi mã nguồn và thích tìm hiểu công nghệ vi mạch.",
            weaknesses_to_improve="Kỹ năng thuyết trình trước đám đông cần tự tin hơn.",
            passionate_interests="Lập trình web, chế tạo mô hình robot Arduino và đọc tin tức AI.",
            dream_career="Kỹ sư Trí tuệ Nhân tạo hoặc Kỹ sư Thiết kế Vi mạch Bán dẫn.",
            parent_wishes="Bố mẹ định hướng vào ĐH Bách Khoa Hà Nội hoặc ĐHQG Hà Nội.",
            preferred_region="Miền Bắc",
            budget_level="Công lập tự chủ"
        )
    )

    profile = evaluate_full_survey(sample_sub)
    profile_dict = profile.model_dump()
    await supabase_service.save_student_profile(profile_dict)
    return {"success": True, "data": profile_dict}
