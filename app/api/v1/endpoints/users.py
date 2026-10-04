from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from app.services.supabase_service import supabase_service
from app.schemas.user import (
    UserProfileRequest,
    UserProfileResponse,
    AcademicRecordSaveRequest,
    BookmarkToggleRequest,
    WishlistItemResponse,
    UserDashboardSummaryResponse
)

router = APIRouter()

@router.post("/profile", response_model=UserProfileResponse, summary="Tạo hoặc cập nhật thông tin học sinh")
async def create_or_update_profile(payload: UserProfileRequest):
    """
    Lưu trữ hoặc đồng bộ thông tin cá nhân học sinh vào Database.
    Hỗ trợ cả Supabase PostgreSQL và local cache zero-downtime.
    """
    user_dict = payload.model_dump(exclude_none=True)
    saved = await supabase_service.create_or_update_user(user_dict)
    return UserProfileResponse(
        id=saved.get("id"),
        email=saved.get("email"),
        full_name=saved.get("full_name", ""),
        phone_number=saved.get("phone_number"),
        school_name=saved.get("school_name"),
        province=saved.get("province"),
        grade=saved.get("grade", 12),
        target_block=saved.get("target_block", "A00"),
        created_at=saved.get("created_at"),
        updated_at=saved.get("updated_at")
    )

@router.get("/profile/{user_id}", response_model=UserProfileResponse, summary="Lấy thông tin cá nhân học sinh")
async def get_user_profile(user_id: str):
    user = await supabase_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy học sinh với ID này.")
    return UserProfileResponse(
        id=user.get("id"),
        email=user.get("email"),
        full_name=user.get("full_name", ""),
        phone_number=user.get("phone_number"),
        school_name=user.get("school_name"),
        province=user.get("province"),
        grade=user.get("grade", 12),
        target_block=user.get("target_block", "A00"),
        created_at=user.get("created_at"),
        updated_at=user.get("updated_at")
    )

@router.post("/academic", summary="Lưu hồ sơ học thuật & điểm học bạ THPT")
async def save_academic_record(payload: AcademicRecordSaveRequest):
    """
    Lưu điểm thi dự kiến và điểm học bạ (GPA 10, 11, 12, tổng điểm tổ hợp môn, chứng chỉ IELTS).
    """
    acad_dict = payload.model_dump()
    saved = await supabase_service.save_academic_record(acad_dict)
    return {
        "success": True,
        "message": "Đã lưu trữ hồ sơ học bạ và điểm học thuật thành công.",
        "record": saved
    }

@router.get("/academic/{user_id}", summary="Lấy hồ sơ học thuật của học sinh")
async def get_academic_record(user_id: str):
    record = await supabase_service.get_academic_record(user_id)
    if not record:
        raise HTTPException(status_code=404, detail="Chưa có hồ sơ học bạ cho học sinh này.")
    return {
        "success": True,
        "record": record
    }

@router.post("/wishlist/toggle", summary="Thêm hoặc xóa trường/ngành khỏi danh sách nguyện vọng yêu thích")
async def toggle_wishlist_item(payload: BookmarkToggleRequest):
    result = await supabase_service.toggle_bookmark(
        user_id=payload.user_id,
        university_code=payload.university_code,
        major_code=payload.major_code,
        uni_name=payload.university_name or "",
        major_name=payload.major_name or "",
        cutoff=payload.cutoff_score_2025 or 25.0
    )
    return result

@router.get("/wishlist/{user_id}", response_model=List[WishlistItemResponse], summary="Xem danh sách trường/ngành đã lưu")
async def get_user_wishlist(user_id: str):
    items = await supabase_service.get_user_wishlist(user_id)
    return [
        WishlistItemResponse(
            id=item.get("id", ""),
            user_id=item.get("user_id", user_id),
            university_code=item.get("university_code", ""),
            major_code=item.get("major_code", ""),
            university_name=item.get("university_name", ""),
            major_name=item.get("major_name", ""),
            cutoff_score_2025=float(item.get("cutoff_score_2025", 25.0)),
            created_at=item.get("created_at", "")
        )
        for item in items
    ]

@router.get("/dashboard/{user_id}", response_model=UserDashboardSummaryResponse, summary="Dashboard tổng hợp tiến độ cá nhân của học sinh")
async def get_user_dashboard(user_id: str):
    """
    Trả về toàn bộ tổng quan học sinh: Thông tin cá nhân, hồ sơ học bạ, mã Holland, số nguyện vọng đã lưu.
    """
    user_data = await supabase_service.get_user_by_id(user_id)
    acad_data = await supabase_service.get_academic_record(user_id)
    wishlist_data = await supabase_service.get_user_wishlist(user_id)
    profile_data = await supabase_service.get_student_profile(user_id)

    user_resp = None
    if user_data:
        user_resp = UserProfileResponse(
            id=user_data.get("id"),
            email=user_data.get("email"),
            full_name=user_data.get("full_name", ""),
            phone_number=user_data.get("phone_number"),
            school_name=user_data.get("school_name"),
            province=user_data.get("province"),
            grade=user_data.get("grade", 12),
            target_block=user_data.get("target_block", "A00"),
            created_at=user_data.get("created_at"),
            updated_at=user_data.get("updated_at")
        )

    wishlist_items = [
        WishlistItemResponse(
            id=item.get("id", ""),
            user_id=item.get("user_id", user_id),
            university_code=item.get("university_code", ""),
            major_code=item.get("major_code", ""),
            university_name=item.get("university_name", ""),
            major_name=item.get("major_name", ""),
            cutoff_score_2025=float(item.get("cutoff_score_2025", 25.0)),
            created_at=item.get("created_at", "")
        )
        for item in wishlist_data
    ]

    holland_code = None
    if profile_data:
        holland_code = profile_data.get("holland", {}).get("holland_code")

    return UserDashboardSummaryResponse(
        user=user_resp,
        academic_record=acad_data,
        career_profile_id=profile_data.get("id") if profile_data else None,
        holland_code=holland_code,
        wishlist_count=len(wishlist_items),
        wishlist_items=wishlist_items,
        total_surveys_completed=1 if profile_data else 0
    )
