import json
import os
from typing import List, Dict, Any, Optional
from app.schemas.profile import StudentCareerProfile
from app.schemas.recommendation import (
    UniversityRecommendationItem,
    RecommendationResponse
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def load_json_file(filename: str):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

UNIVERSITIES_DATABASE = load_json_file("universities_database.json")
REGULATIONS_2026 = load_json_file("regulations_2026.json")

def generate_recommendations(
    profile: StudentCareerProfile,
    preferred_region: Optional[str] = None,
    max_tuition: Optional[float] = None
) -> RecommendationResponse:
    student_score = profile.academic.estimated_exam_score
    target_block = profile.academic.target_block.upper()
    top_field_codes = [m.code for m in profile.top_majors]

    # Check for IELTS bonus/conversion
    effective_score = student_score
    if profile.academic.english_score and profile.academic.english_score >= 6.5:
        # Many top schools give priority conversion or bonus
        effective_score = min(30.0, student_score + 0.5)

    all_options: List[UniversityRecommendationItem] = []

    for uni in UNIVERSITIES_DATABASE:
        # Check region filter
        uni_region = uni.get("region", "")
        if preferred_region and preferred_region not in ["Tất cả", "Toàn quốc"]:
            if preferred_region == "Miền Bắc" and uni_region not in ["North", "National"]:
                continue
            elif preferred_region == "Miền Trung" and uni_region not in ["Central", "National"]:
                continue
            elif preferred_region == "Miền Nam" and uni_region not in ["South", "National"]:
                continue

        # Check tuition filter
        if max_tuition and uni.get("tuition_number", 0) > max_tuition:
            continue

        for major in uni.get("majors", []):
            m_block = major.get("block", "")
            # Check block compatibility or general block
            if m_block != target_block and target_block not in ["ALL", ""]:
                # allow D01 / A01 overlaps or A00
                if not (target_block in ["A00", "A01"] and m_block in ["A00", "A01"]):
                    continue

            pred_score = major.get("score_pred_2026", major.get("score_2025", 25.0))
            delta = round(effective_score - pred_score, 2)

            # Categorize into Dream, Target, Safety
            if -2.5 <= delta < -0.4:
                tier = "Mơ ước (Dream)"
                reason = f"Điểm chuẩn dự kiến ({pred_score}) cao hơn mức hiện tại {abs(delta)} điểm. Là mục tiêu bứt phá lý tưởng đặt ở Nguyện vọng 1."
            elif -0.4 <= delta <= 1.2:
                tier = "Vừa sức (Target)"
                reason = f"Điểm chuẩn dự kiến ({pred_score}) tiệm cận rất sát năng lực hiện tại của em. Khả năng trúng tuyển cao (65% - 80%)."
            elif delta > 1.2 and delta <= 7.0:
                tier = "An toàn (Safety)"
                reason = f"Em đang có ưu thế vượt chuẩn {delta} điểm. Đặt ở nhóm nguyện vọng an toàn để bảo đảm 100% đỗ đại học."
            else:
                continue

            all_options.append(UniversityRecommendationItem(
                university_id=uni["id"],
                university_name=uni["name"],
                university_code=uni["code"],
                major_code=major["code"],
                major_name=major["name"],
                field_code=major.get("field_code", "748"),
                region=uni["region"],
                location=uni["location"],
                exam_block=m_block,
                benchmark_2024=major.get("score_2024", 0.0),
                benchmark_2025=major.get("score_2025", 0.0),
                benchmark_pred_2026=pred_score,
                student_score=effective_score,
                score_delta=delta,
                tier=tier,
                tuition_range=uni.get("tuition_range", ""),
                admission_methods=uni.get("admission_methods", []),
                ielts_policy=uni.get("ielts_policy", ""),
                official_website=uni.get("website", ""),
                verification_source=uni.get("verification_source", "Cấp 1 - Chính thức"),
                match_reason=reason
            ))

    dream_tier = [item for item in all_options if "Mơ ước" in item.tier]
    target_tier = [item for item in all_options if "Vừa sức" in item.tier]
    safety_tier = [item for item in all_options if "An toàn" in item.tier]

    # Sort each tier by relevance and score delta
    dream_tier.sort(key=lambda x: abs(x.score_delta))
    target_tier.sort(key=lambda x: abs(x.score_delta))
    safety_tier.sort(key=lambda x: x.score_delta)

    # Strategy advice based on student score
    strategic_advice = (
        f"Chiến lược phân bổ nguyện vọng cho mức điểm {effective_score} khối {target_block}: "
        f"Nên chia danh sách đăng ký làm 3 tầng: "
        f"1-2 Nguyện vọng Mơ ước (Dream) để thử thách bản thân ở trường top; "
        f"2-3 Nguyện vọng Vừa sức (Target) có xác suất trúng tuyển cao nhất; "
        f"1-2 Nguyện vọng An toàn (Safety) với khoảng cách an toàn trên 1.5 điểm để khóa chân trúng tuyển."
    )

    return RecommendationResponse(
        student_name=profile.student_name,
        target_block=target_block,
        estimated_score=effective_score,
        dream_tier=dream_tier[:5],
        target_tier=target_tier[:6],
        safety_tier=safety_tier[:5],
        strategic_advice=strategic_advice
    )

def compare_options(selected_options: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    results = []
    for opt in selected_options:
        uni_id = opt.get("university_id")
        major_code = opt.get("major_code")

        uni = next((u for u in UNIVERSITIES_DATABASE if u["id"] == uni_id or u["code"] == uni_id), None)
        if not uni:
            continue

        major = next((m for m in uni.get("majors", []) if m["code"] == major_code or m["name"] == opt.get("major_name")), None)
        if not major and uni.get("majors"):
            major = uni["majors"][0]

        results.append({
            "university_name": uni["name"],
            "university_code": uni["code"],
            "type": uni["type"],
            "location": uni["location"],
            "tuition_range": uni["tuition_range"],
            "quota_2026": uni["quota_2026"],
            "major_name": major["name"] if major else "Đa ngành",
            "major_code": major["code"] if major else "",
            "benchmark_2024": major.get("score_2024", 0.0) if major else 0.0,
            "benchmark_2025": major.get("score_2025", 0.0) if major else 0.0,
            "benchmark_pred_2026": major.get("score_pred_2026", 0.0) if major else 0.0,
            "admission_methods": uni["admission_methods"],
            "ielts_policy": uni["ielts_policy"],
            "website": uni["website"],
            "verification_source": uni["verification_source"]
        })
    return results
