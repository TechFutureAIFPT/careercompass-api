import os
import json
import math
import re
from typing import Dict, Any, List, Optional, Tuple

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
ROOT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")

class RAGDocumentChunk:
    def __init__(self, id: str, title: str, category: str, content: str, source: str, metadata: Optional[Dict[str, Any]] = None):
        self.id = id
        self.title = title
        self.category = category
        self.content = content
        self.source = source
        self.metadata = metadata or {}
        self.tokens = self._tokenize(content)

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r'[^\w\s]', ' ', text.lower())
        return [w for w in cleaned.split() if len(w) > 1]

class AdmissionRAGService:
    def __init__(self):
        self.chunks: List[RAGDocumentChunk] = []
        self.idf: Dict[str, float] = {}
        self._build_corpus()

    def _add_chunk(self, id: str, title: str, category: str, content: str, source: str, metadata: Optional[Dict[str, Any]] = None):
        chunk = RAGDocumentChunk(id, title, category, content, source, metadata)
        self.chunks.append(chunk)

    def _build_corpus(self):
        # 1. Ingest Regulations 2026 (Circular 06/2026/TT-BGDĐT)
        reg_path = os.path.join(DATA_DIR, "regulations_2026.json")
        if os.path.exists(reg_path):
            with open(reg_path, "r", encoding="utf-8") as f:
                regs = json.load(f)

            if isinstance(regs, dict):
                for key, val in regs.items():
                    content = json.dumps(val, ensure_ascii=False) if isinstance(val, (dict, list)) else str(val)
                    self._add_chunk(
                        id=f"REG_{key}",
                        title=f"Quy chế Tuyển sinh 2026 - {key}",
                        category="regulations_2026",
                        content=f"Quy định Bộ GD&ĐT 2026 ({key}): {content}",
                        source="Thông tư 06/2026/TT-BGDĐT",
                        metadata={"type": "regulation", "section": key}
                    )
            elif isinstance(regs, list):
                for idx, r in enumerate(regs):
                    self._add_chunk(
                        id=f"REG_{idx}",
                        title=r.get("title", f"Quy định {idx+1}"),
                        category="regulations_2026",
                        content=r.get("content", str(r)),
                        source="Thông tư 06/2026/TT-BGDĐT",
                        metadata=r
                    )

        # 2. Ingest University Admissions & Benchmarks
        uni_path = os.path.join(DATA_DIR, "universities_database.json")
        if os.path.exists(uni_path):
            with open(uni_path, "r", encoding="utf-8") as f:
                unis = json.load(f)

            for u in unis:
                # University profile chunk
                uni_overview = (
                    f"Trường {u['name']} (Mã trường: {u['code']}). "
                    f"Khu vực: {u.get('location')} ({u.get('region')}). "
                    f"Học phí: {u.get('tuition_range')}. Chỉ tiêu tuyển sinh 2026: {u.get('quota_2026')} sinh viên. "
                    f"Phương thức xét tuyển chính: {', '.join(u.get('admission_methods', []))}. "
                    f"Chính sách quy đổi chứng chỉ ngoại ngữ IELTS: {u.get('ielts_policy', 'Theo đề án riêng')}."
                )
                self._add_chunk(
                    id=f"UNI_{u['code']}_OVERVIEW",
                    title=f"Đề án Tuyển sinh: {u['name']} ({u['code']})",
                    category="university_scheme",
                    content=uni_overview,
                    source=f"Đề án tuyển sinh chính thức {u['code']} 2026",
                    metadata={"university_code": u["code"], "type": "university"}
                )

                # Major cutoff benchmark chunks
                for prog in u.get("majors", []):
                    prog_content = (
                        f"Ngành đào tạo: {prog.get('name')} (Mã ngành: {prog.get('code')}) tại {u['name']} ({u['code']}). "
                        f"Tổ hợp môn xét tuyển: {prog.get('block', 'A00')}. "
                        f"Điểm chuẩn năm 2024: {prog.get('score_2024')} điểm. "
                        f"Điểm chuẩn năm 2025: {prog.get('score_2025')} điểm. "
                        f"Dự báo điểm chuẩn kỳ thi tốt nghiệp 2026: {prog.get('score_pred_2026')} điểm. "
                        f"Nhu cầu điểm học bạ THPT: từ 8.0 - 9.0 tùy đợt xét tuyển sớm."
                    )
                    self._add_chunk(
                        id=f"BENCHMARK_{u['code']}_{prog.get('code')}",
                        title=f"Điểm chuẩn {prog.get('name')} - {u['code']}",
                        category="cutoff_benchmarks",
                        content=prog_content,
                        source=f"Điểm chuẩn tuyển sinh {u['code']} & Tuyensinh247",
                        metadata={"university_code": u["code"], "major_code": prog.get("code")}
                    )

        # 3. Ingest Majors Database & Career Profiles
        majors_path = os.path.join(DATA_DIR, "majors_database.json")
        if os.path.exists(majors_path):
            with open(majors_path, "r", encoding="utf-8") as f:
                majors = json.load(f)

            for m in majors:
                m_content = (
                    f"Nhóm ngành: {m['name']} (Mã lĩnh vực: {m['code']}). "
                    f"Mô tả chương trình: {m.get('description')}. "
                    f"Tổ hợp môn thi THPT: {', '.join(m.get('exam_blocks', []))}. "
                    f"Đặc tính hướng nghiệp Holland phù hợp: Nhóm {m.get('holland_code')} (Chủ đạo: {m.get('primary_holland')}). "
                    f"Vị trí nghề nghiệp tiêu biểu: {', '.join(m.get('popular_careers', []))}. "
                    f"Mức lương khởi điểm và phát triển: {m.get('salary_range')}. "
                    f"Xu hướng thị trường lao động 2026 - 2030: {m.get('growth_outlook')}."
                )
                self._add_chunk(
                    id=f"MAJOR_{m['code']}",
                    title=f"Định hướng Nghề nghiệp: {m['name']}",
                    category="major_profiles",
                    content=m_content,
                    source="Tổng cục Giáo dục Nghề nghiệp & Bộ LĐ-TB&XH",
                    metadata={"major_code": m["code"]}
                )

        # 4. Ingest Song An Assessment Reference Materials
        holland_ref = (
            "Khung lý thuyết Trắc nghiệm Holland RIASEC chuẩn hóa bởi Hướng nghiệp Sông An: "
            "R (Realistic - Kỹ thuật/Thực tế): phù hợp công cụ, kỹ thuật, máy móc, thể thao; "
            "I (Investigative - Nghiên cứu): tư duy logic, khoa học, phân tích dữ liệu, y dược, vũ trụ; "
            "A (Artistic - Nghệ thuật): sáng tạo, hội họa, âm nhạc, thiết kế, truyền thông; "
            "S (Social - Xã hội): thấu cảm, tâm lý, giáo dục, y tế cộng đồng, tư vấn; "
            "E (Enterprising - Quản lý): kinh doanh, thương mại, lãnh đạo, tài chính, đàm phán; "
            "C (Conventional - Nghiệp vụ): tổ chức, kế toán, văn phòng, ngân hàng, quản trị hồ sơ."
        )
        self._add_chunk(
            id="SONGAN_HOLLAND_THEORY",
            title="Lý thuyết Đặc tính nghề nghiệp Holland RIASEC",
            category="holland_assessment",
            content=holland_ref,
            source="Doanh nghiệp Xã hội Hướng nghiệp Sông An (CC BY-ND 4.0)"
        )

        # Calculate IDF for TF-IDF ranking
        self._calculate_idf()

    def _calculate_idf(self):
        doc_count = len(self.chunks)
        df: Dict[str, int] = {}
        for c in self.chunks:
            seen_words = set(c.tokens)
            for w in seen_words:
                df[w] = df.get(w, 0) + 1

        for w, count in df.items():
            self.idf[w] = math.log((doc_count + 1) / (count + 1)) + 1.0

    def search_relevant_chunks(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None
    ) -> List[Tuple[RAGDocumentChunk, float]]:
        cleaned_query = re.sub(r'[^\w\s]', ' ', query.lower())
        query_words = [w for w in cleaned_query.split() if len(w) > 1]

        if not query_words:
            return [(c, 0.5) for c in self.chunks[:top_k]]

        scored: List[Tuple[RAGDocumentChunk, float]] = []
        for c in self.chunks:
            if category_filter and c.category != category_filter:
                continue

            score = 0.0
            doc_len = len(c.tokens) or 1
            for qw in query_words:
                tf = c.tokens.count(qw) / doc_len
                idf_val = self.idf.get(qw, 1.0)
                score += tf * idf_val

            # Boost if query keyword appears in title
            for qw in query_words:
                if qw in c.title.lower():
                    score += 0.4

            if score > 0.001:
                scored.append((c, round(score, 4)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def build_grounded_rag_context(self, query: str, top_k: int = 4) -> Tuple[str, List[Dict[str, str]]]:
        results = self.search_relevant_chunks(query, top_k=top_k)
        if not results:
            return "", []

        context_lines = []
        citations = []

        for idx, (chunk, score) in enumerate(results):
            context_lines.append(f"[{idx+1}] {chunk.title} ({chunk.source}):\n{chunk.content}")
            citations.append({
                "id": str(idx+1),
                "title": chunk.title,
                "url": chunk.source,
                "domain": chunk.category,
                "snippet": chunk.content[:200] + "..."
            })

        return "\n\n".join(context_lines), citations

rag_service = AdmissionRAGService()
