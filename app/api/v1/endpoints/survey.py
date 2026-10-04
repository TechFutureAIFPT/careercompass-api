from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.schemas.survey import SurveySubmission
from app.schemas.profile import StudentCareerProfile
from app.services.scoring_engine import (
    evaluate_full_survey,
    HOLLAND_QUESTIONS,
    SCCT_QUESTIONS,
    GARDNER_QUESTIONS,
    DISC_QUESTIONS
)
from app.services.supabase_service import supabase_service

router = APIRouter()

@router.get("/questions", summary="Lấy toàn bộ ngân hàng câu hỏi khảo sát đa chiều")
async def get_survey_questions() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "holland_riasec": HOLLAND_QUESTIONS,
            "scct_self_efficacy": SCCT_QUESTIONS,
            "gardner_multi_intelligence": GARDNER_QUESTIONS,
            "disc_personality": DISC_QUESTIONS,
            "total_questions": len(HOLLAND_QUESTIONS) + len(SCCT_QUESTIONS) + len(GARDNER_QUESTIONS) + len(DISC_QUESTIONS)
        }
    }

@router.post("/submit", response_model=Dict[str, Any], summary="Nộp bài khảo sát và tính toán Hồ sơ Hướng nghiệp cá nhân")
async def submit_survey(submission: SurveySubmission):
    try:
        profile: StudentCareerProfile = evaluate_full_survey(submission)
        profile_dict = profile.model_dump()
        await supabase_service.save_student_profile(profile_dict)
        return {
            "success": True,
            "data": profile_dict,
            "message": "Đã chấm điểm và tạo Hồ sơ Hướng nghiệp Cá nhân hóa thành công!"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi đánh giá hồ sơ khảo sát: {str(e)}")
