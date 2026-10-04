import json
import os
from typing import Dict, List, Tuple
from app.schemas.survey import SurveySubmission
from app.schemas.profile import (
    HollandScoreResult,
    SCCTQuadrantItem,
    GardnerScoreResult,
    DISCScoreResult,
    MajorMatchResult,
    StudentCareerProfile
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def load_json_file(filename: str):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

HOLLAND_QUESTIONS = load_json_file("holland_questions.json")
SCCT_QUESTIONS = load_json_file("scct_questions.json")
GARDNER_QUESTIONS = load_json_file("gardner_questions.json")
DISC_QUESTIONS = load_json_file("disc_questions.json")
MAJORS_DATABASE = load_json_file("majors_database.json")

TRAIT_NAMES = {
    "R": "Kỹ thuật / Thực tế (Realistic)",
    "I": "Nghiên cứu / Khám phá (Investigative)",
    "A": "Nghệ thuật / Sáng tạo (Artistic)",
    "S": "Xã hội / Giúp đỡ (Social)",
    "E": "Quản lý / Thuyết phục (Enterprising)",
    "C": "Nghiệp vụ / Quy củ (Conventional)"
}

def calculate_holland(answers: Dict[str, int]) -> HollandScoreResult:
    scores = {"R": 0.0, "I": 0.0, "A": 0.0, "S": 0.0, "E": 0.0, "C": 0.0}
    counts = {"R": 0, "I": 0, "A": 0, "S": 0, "E": 0, "C": 0}

    for q in HOLLAND_QUESTIONS:
        group = q.get("group")
        qid = q.get("id")
        if group in scores:
            counts[group] += 1
            rating = answers.get(qid, 3)
            scores[group] += rating

    total_possible = {k: counts[k] * 5 for k in scores}
    percentages = {
        k: round((scores[k] / total_possible[k]) * 100, 1) if total_possible[k] > 0 else 50.0
        for k in scores
    }

    # Sort descending to get top 3 codes
    sorted_groups = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
    holland_code = "".join(sorted_groups[:3])
    primary_trait = TRAIT_NAMES.get(sorted_groups[0], "Nghiên cứu")

    return HollandScoreResult(
        scores=scores,
        percentages=percentages,
        holland_code=holland_code,
        primary_trait=primary_trait
    )

def calculate_scct(holland_scores: Dict[str, float], scct_answers: Dict[str, int]) -> List[SCCTQuadrantItem]:
    confidence_scores = {"R": 0.0, "I": 0.0, "A": 0.0, "S": 0.0, "E": 0.0, "C": 0.0}
    counts = {"R": 0, "I": 0, "A": 0, "S": 0, "E": 0, "C": 0}

    for q in SCCT_QUESTIONS:
        group = q.get("group")
        qid = q.get("id")
        if group in confidence_scores:
            counts[group] += 1
            confidence_scores[group] += scct_answers.get(qid, 3)

    # Calculate dynamic question counts per group
    holland_counts = {}
    for q in HOLLAND_QUESTIONS:
        grp = q.get("group")
        if grp:
            holland_counts[grp] = holland_counts.get(grp, 0) + 1

    scct_counts = {}
    for q in SCCT_QUESTIONS:
        grp = q.get("group")
        if grp:
            scct_counts[grp] = scct_counts.get(grp, 0) + 1

    results = []
    for g in ["R", "I", "A", "S", "E", "C"]:
        # Normalized average on scale 1-5
        h_cnt = max(holland_counts.get(g, 1), 1)
        s_cnt = max(scct_counts.get(g, 1), 1)
        interest_avg = round(holland_scores.get(g, 3.0 * h_cnt) / float(h_cnt), 2)
        conf_avg = round(confidence_scores.get(g, 3.0 * s_cnt) / float(s_cnt), 2)

        # Cutoff threshold = 3.2
        is_high_interest = interest_avg >= 3.2
        is_high_conf = conf_avg >= 3.2

        if is_high_interest and is_high_conf:
            quadrant = "Vùng Hành động (Action Zone)"
            advice = "Sở thích cao và Năng lực tự tin cao. Đây là hướng đi lý tưởng nhất để em đặt làm Nguyện vọng 1 và đầu tư chuyên sâu."
        elif is_high_interest and not is_high_conf:
            quadrant = "Vùng Cần rèn luyện (Development Zone)"
            advice = "Em rất say mê nhưng hiện còn thiếu tự tin về kỹ năng. Cần chủ động tham gia các khóa học nâng cao năng lực để bù đắp sự tự ti."
        elif not is_high_interest and is_high_conf:
            quadrant = "Vùng Dự phòng (Backup Zone)"
            advice = "Em có kỹ năng tốt nhưng chưa thực sự đam mê. Phù hợp làm phương án dự phòng an toàn hoặc kỹ năng hỗ trợ công việc chính."
        else:
            quadrant = "Vùng Hạn chế (Avoid Zone)"
            advice = "Cả sở thích và niềm tin năng lực đều ở mức thấp. Nên hạn chế chọn nhóm ngành này để tránh áp lực và chán nản khi học đại học."

        results.append(SCCTQuadrantItem(
            group=g,
            dimension_name=TRAIT_NAMES.get(g, g),
            interest_score=interest_avg,
            confidence_score=conf_avg,
            quadrant=quadrant,
            advice=advice
        ))

    return results

def calculate_gardner(answers: Dict[str, int]) -> GardnerScoreResult:
    scores = {
        "linguistic": 0.0,
        "logical_math": 0.0,
        "spatial": 0.0,
        "musical": 0.0,
        "bodily_kinesthetic": 0.0,
        "interpersonal": 0.0,
        "intrapersonal": 0.0,
        "naturalistic": 0.0
    }
    counts = {k: 0 for k in scores}

    name_map = {
        "linguistic": "Ngôn ngữ",
        "logical_math": "Logic - Toán học",
        "spatial": "Không gian - Thị giác",
        "musical": "Âm nhạc - Thính giác",
        "bodily_kinesthetic": "Vận động cơ thể",
        "interpersonal": "Tương tác giao tiếp",
        "intrapersonal": "Nội tâm - Tự nhận thức",
        "naturalistic": "Tự nhiên - Sinh thái"
    }

    for q in GARDNER_QUESTIONS:
        t = q.get("type")
        qid = q.get("id")
        if t in scores:
            counts[t] += 1
            scores[t] += answers.get(qid, 3)

    # Average score out of 5
    avg_scores = {k: round(scores[k] / max(counts[k], 1), 2) for k in scores}
    sorted_types = sorted(avg_scores.keys(), key=lambda k: avg_scores[k], reverse=True)
    top_3 = [name_map.get(t, t) for t in sorted_types[:3]]

    top1 = sorted_types[0]
    if top1 in ["logical_math", "spatial"]:
        learning_advice = "Em học hiệu quả nhất thông qua sơ đồ tư duy (Mindmap), bài tập ứng dụng thực tế, giải quyết vấn đề số liệu và mô hình 3D trực quan."
    elif top1 in ["linguistic", "interpersonal"]:
        learning_advice = "Em tiếp thu kiến thức tốt nhất khi đọc - tóm tắt tài liệu, thảo luận nhóm, tranh biện và giảng giải lại cho bạn bè."
    elif top1 in ["intrapersonal"]:
        learning_advice = "Em học tập năng suất nhất trong không gian yên tĩnh, có thời gian tự nghiên cứu sâu và phản tư độc lập."
    else:
        learning_advice = "Em phát huy tối đa khi kết hợp học tập qua thực hành dự án, quan sát hiện trường thực tế và ứng dụng trực tiếp."

    return GardnerScoreResult(
        scores=avg_scores,
        top_intelligences=top_3,
        learning_style_advice=learning_advice
    )

def calculate_disc(answers: Dict[str, int]) -> DISCScoreResult:
    scores = {"D": 0.0, "I": 0.0, "S": 0.0, "C": 0.0}
    counts = {"D": 0, "I": 0, "S": 0, "C": 0}

    for q in DISC_QUESTIONS:
        trait = q.get("trait")
        qid = q.get("id")
        if trait in scores:
            counts[trait] += 1
            scores[trait] += answers.get(qid, 3)

    avg_scores = {k: round(scores[k] / max(counts[k], 1), 2) for k in scores}
    dominant_trait = max(avg_scores.keys(), key=lambda k: avg_scores[k])

    disc_descriptions = {
        "D": ("Thống lĩnh (Dominance)", "Phong cách quyết đoán, hướng tới kết quả cao và chấp nhận thách thức. Em phù hợp với vị trí quản lý, khởi nghiệp, trưởng nhóm công nghệ hoặc đàm phán chiến lược."),
        "I": ("Ảnh hưởng (Influence)", "Phong cách truyền cảm hứng, nhiệt huyết và kết nối quan hệ xã hội. Em rất mạnh khi làm việc trong môi trường truyền thông, marketing, đối ngoại, sáng tạo hoặc đào tạo nhân sự."),
        "S": ("Kiên định (Steadiness)", "Phong cách kiên nhẫn, điềm tĩnh, đề cao sự hòa thuận và gắn kết lâu dài. Em phù hợp với môi trường làm việc ổn định, dịch vụ chăm sóc y tế, giáo dục, tâm lý học và nghiên cứu bền bỉ."),
        "C": ("Tuân thủ (Conscientiousness)", "Phong cách logic, chính xác, kỷ luật và phân tích hệ thống dữ liệu. Em xuất sắc trong các ngành kỹ thuật phần mềm, bán dẫn, kiểm toán, luật kinh tế và phân tích tài chính.")
    }

    trait_name, workplace_style = disc_descriptions.get(dominant_trait, ("Cân bằng", "Linh hoạt"))

    return DISCScoreResult(
        scores=avg_scores,
        dominant_trait=f"{dominant_trait} - {trait_name}",
        workplace_style=workplace_style
    )

def match_majors(
    holland_res: HollandScoreResult,
    gardner_res: GardnerScoreResult,
    academic_block: str,
    favorite_subjects: List[str]
) -> List[MajorMatchResult]:
    matched = []
    holland_code = holland_res.holland_code
    primary_h = holland_code[0] if holland_code else "I"
    secondary_h = holland_code[1] if len(holland_code) > 1 else "R"

    for major in MAJORS_DATABASE:
        score = 50.0  # Base score
        m_holland = major.get("holland_code", "")
        m_primary = major.get("primary_holland", "")
        m_secondary = major.get("secondary_holland", "")
        blocks = major.get("exam_blocks", [])

        # Holland Primary match (+25%)
        if m_primary == primary_h:
            score += 25.0
        elif m_primary == secondary_h:
            score += 15.0
        elif m_primary in holland_code:
            score += 10.0

        # Secondary Holland match (+10%)
        if m_secondary in holland_code:
            score += 10.0

        # Exam Block match (+10%)
        if academic_block in blocks:
            score += 10.0

        # Gardner intelligence match (+5%)
        top_types = [t.lower() for t in gardner_res.top_intelligences]
        m_gardner = major.get("gardner_type", "")
        if any(m_gardner in t for t in top_types):
            score += 5.0

        score = min(score, 98.0)

        reason = f"Phù hợp với nhóm tính cách {m_primary} ({TRAIT_NAMES.get(m_primary, '')}) và tổ hợp thi {academic_block} của em."
        matched.append(MajorMatchResult(
            code=major["code"],
            name=major["name"],
            match_score=round(score, 1),
            holland_code=m_holland,
            popular_careers=major.get("popular_careers", []),
            salary_range=major.get("salary_range", ""),
            growth_outlook=major.get("growth_outlook", ""),
            suitable_reason=reason
        ))

    matched.sort(key=lambda m: m.match_score, reverse=True)
    return matched[:6]

def evaluate_full_survey(submission: SurveySubmission) -> StudentCareerProfile:
    import uuid
    from datetime import datetime

    holland_res = calculate_holland(submission.holland_answers)
    scct_res = calculate_scct(holland_res.scores, submission.scct_answers)
    gardner_res = calculate_gardner(submission.gardner_answers)
    disc_res = calculate_disc(submission.disc_answers)

    top_majors = match_majors(
        holland_res=holland_res,
        gardner_res=gardner_res,
        academic_block=submission.academic.target_block,
        favorite_subjects=submission.academic.favorite_subjects
    )

    # Calculate high school transcript averages if not explicitly populated
    ac = submission.academic
    gpas = [g for g in [ac.gpa_10, ac.gpa_11, ac.gpa_12] if g is not None]
    if gpas and ac.transcript_gpa_overall is None:
        ac.transcript_gpa_overall = round(sum(gpas) / len(gpas), 2)

    if ac.transcript_subject_scores and ac.transcript_block_score is None:
        ac.transcript_block_score = round(sum(ac.transcript_subject_scores.values()), 2)

    profile_id = f"PRF_{uuid.uuid4().hex[:8].upper()}"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Generate professional pedagogical summary
    action_quadrants = [item.dimension_name for item in scct_res if "Hành động" in item.quadrant]
    action_str = ", ".join(action_quadrants) if action_quadrants else holland_res.primary_trait

    transcript_info = ""
    if ac.transcript_gpa_overall:
        transcript_info = f" Học bạ THPT đạt GPA {ac.transcript_gpa_overall} (Xếp loại {ac.academic_ranking}), mở ra cơ hội cạnh tranh lớn cho phương thức xét học bạ sớm."

    ai_summary = (
        f"Học sinh {submission.student_name} sở hữu mã Holland chủ đạo là {holland_res.holland_code} "
        f"với xu hướng nghề nghiệp nổi bật ở nhóm {holland_res.primary_trait}. "
        f"Theo ma trận niềm tin năng lực SCCT, lĩnh vực thuộc Vùng Hành động tự tin nhất của em là: {action_str}. "
        f"Về phong cách làm việc, em thể hiện xu hướng {disc_res.dominant_trait}. "
        f"Với điểm thi dự kiến {submission.academic.estimated_exam_score} khối {submission.academic.target_block},{transcript_info} "
        f"các nhóm ngành đào tạo có độ tương thích cao nhất gồm: "
        f"{', '.join([m.name for m in top_majors[:3]])}."
    )


    return StudentCareerProfile(
        id=profile_id,
        created_at=created_at,
        student_name=submission.student_name,
        school_name=submission.school_name,
        academic=submission.academic,
        qualitative=submission.qualitative,
        holland=holland_res,
        scct=scct_res,
        gardner=gardner_res,
        disc=disc_res,
        top_majors=top_majors,
        ai_executive_summary=ai_summary
    )
