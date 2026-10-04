from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from app.schemas.profile import StudentCareerProfile
from app.schemas.recommendation import RecommendationResponse, ComparisonRequest
from app.services.recommendation_engine import generate_recommendations, compare_options
from app.services.supabase_service import supabase_service

router = APIRouter()

@router.post("/generate", response_model=Dict[str, Any], summary="Tạo danh mục nguyện vọng Mơ ước - Vừa sức - An toàn")
async def get_university_recommendations(
    profile: StudentCareerProfile,
    region: Optional[str] = Query(None, description="Khu vực lọc: Miền Bắc, Miền Trung, Miền Nam, Toàn quốc"),
    max_tuition: Optional[float] = Query(None, description="Học phí tối đa (triệu VNĐ/năm)")
):
    try:
        rec_res = generate_recommendations(
            profile=profile,
            preferred_region=region or profile.qualitative.preferred_region,
            max_tuition=max_tuition
        )
        return {
            "success": True,
            "data": rec_res.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tạo danh mục tư vấn: {str(e)}")

@router.post("/compare", response_model=Dict[str, Any], summary="So sánh đa tiêu chí giữa các trường/ngành (Decision Matrix)")
async def compare_universities(request: ComparisonRequest):
    try:
        matrix_data = compare_options(request.selected_options)
        return {
            "success": True,
            "data": matrix_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi ma trận so sánh: {str(e)}")
