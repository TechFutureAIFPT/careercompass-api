from fastapi import APIRouter
from typing import Dict, Any, List
import os
import json

router = APIRouter()

from app.services.scoring_engine import DATA_DIR

def load_roadmap():
    with open(os.path.join(DATA_DIR, "roadmap_milestones.json"), "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/milestones", summary="Lấy 6 giai đoạn lộ trình hướng nghiệp và tuyển sinh lớp 12")
async def get_roadmap_milestones() -> Dict[str, Any]:
    milestones = load_roadmap()
    return {
        "success": True,
        "total_stages": len(milestones),
        "data": milestones
    }
