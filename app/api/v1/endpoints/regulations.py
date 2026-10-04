from fastapi import APIRouter
from typing import Dict, Any
import os
import json

router = APIRouter()

from app.services.scoring_engine import DATA_DIR

def load_regulations():
    with open(os.path.join(DATA_DIR, "regulations_2026.json"), "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/2026", summary="Chi tiết quy chế tuyển sinh 2026 (Thông tư 06/2026/TT-BGDĐT)")
async def get_regulations_2026() -> Dict[str, Any]:
    regs = load_regulations()
    return {
        "success": True,
        "data": regs,
        "season": "Mùa tuyển sinh 2026",
        "verified": True
    }

@router.get("/conversion", summary="Bảng quy đổi chứng chỉ ngoại ngữ và bài thi ĐGNL/ĐGTD sang thang 30")
async def get_conversion_tables() -> Dict[str, Any]:
    regs = load_regulations()
    return {
        "success": True,
        "data": regs.get("conversion_tables", {})
    }
