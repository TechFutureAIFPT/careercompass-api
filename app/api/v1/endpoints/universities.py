from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
import os
import json

router = APIRouter()

# Path to main_backend/app/data (4 levels up from endpoints -> v1 -> api -> app -> data)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data")

def load_json(name: str):
    path = os.path.join(DATA_DIR, name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

UNIVERSITIES = load_json("universities_database.json")
MAJORS = load_json("majors_database.json")

@router.get("", summary="Tìm kiếm và lọc danh mục các trường đại học")
async def list_universities(
    keyword: Optional[str] = Query(None, description="Từ khóa tên trường hoặc mã trường"),
    region: Optional[str] = Query(None, description="Khu vực: North, Central, South"),
    block: Optional[str] = Query(None, description="Tổ hợp xét tuyển: A00, D01, B00..."),
    max_tuition: Optional[float] = Query(None, description="Mức học phí tối đa (triệu/năm)")
) -> Dict[str, Any]:
    filtered = UNIVERSITIES

    if keyword:
        k = keyword.lower()
        filtered = [
            u for u in filtered
            if k in u["name"].lower() or k in u["code"].lower() or k in u.get("location", "").lower()
        ]

    if region and region != "ALL":
        filtered = [u for u in filtered if u.get("region") == region or u.get("region") == "National"]

    if max_tuition:
        filtered = [u for u in filtered if u.get("tuition_number", 0) <= max_tuition]

    if block and block != "ALL":
        result_unis = []
        for u in filtered:
            has_block = any(m.get("block") == block for m in u.get("majors", []))
            if has_block:
                result_unis.append(u)
        filtered = result_unis

    return {
        "success": True,
        "total": len(filtered),
        "data": filtered
    }

@router.get("/{uni_id}", summary="Lấy chi tiết trường đại học và lịch sử điểm chuẩn")
async def get_university_detail(uni_id: str) -> Dict[str, Any]:
    uni = next((u for u in UNIVERSITIES if u["id"] == uni_id or u["code"] == uni_id), None)
    if not uni:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin trường đại học này")
    return {"success": True, "data": uni}

@router.get("/data/majors", summary="Lấy danh mục 23 nhóm ngành chuẩn GD&ĐT kèm mã Holland")
async def get_all_majors() -> Dict[str, Any]:
    return {
        "success": True,
        "total": len(MAJORS),
        "data": MAJORS
    }
