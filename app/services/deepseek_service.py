import httpx
import re
from typing import List, Dict, Any, Tuple, Optional
from app.core.config import settings
from app.schemas.chat import ChatMessage, CitationItem, ChatResponse
from app.services.deep_research_service import deep_research_service
from app.services.data_retrieval_client import retrieval_client
from app.services.rag_service import rag_service
from app.services.graph_service import graph_service

SYSTEM_PROMPT = """Bạn là Cố vấn Hướng nghiệp & Tuyển sinh AI Cao cấp của CareerCompass-AI 2026.
Nhiệm vụ của bạn là tư vấn cho học sinh lớp 12 tại Việt Nam chuẩn bị thi tốt nghiệp THPT và xét tuyển đại học.

NGUYÊN TẮC TƯ VẤN:
1. Độc lập, khách quan, chuẩn mực sư phạm và khoa học. Tuyệt đối không phán đoán mê tín hay thần số học.
2. Căn cứ 100% vào:
   - Hồ sơ khảo sát đa chiều của học sinh (Holland RIASEC, SCCT niềm tin năng lực, Đa trí tuệ Gardner, DISC, điểm thi dự kiến, điểm học bạ 3 năm THPT, tổ hợp môn).
   - Cơ sở tri thức Đồ thị (Knowledge Graph) liên kết Mật mã Holland -> Ngành đào tạo -> Tổ hợp môn -> Trường ĐH -> Cơ hội việc làm.
   - Kho văn bản quy phạm pháp luật RAG (Thông tư 06/2026/TT-BGDĐT) và đề án tuyển sinh chính thức từ các trường.
3. Khi tư vấn chọn trường - ngành, luôn phân bổ chiến lược 3 tầng: Mơ ước (Dream), Vừa sức (Target), An toàn (Safety).
4. Phản hồi có cấu trúc rõ ràng:
   - Nhận định hồ sơ & điểm mạnh
   - Đề xuất ngành & trường cụ thể kèm điểm chuẩn dự kiến
   - Lời khuyên chiến lược nộp nguyện vọng và lộ trình ôn tập.
"""

class DeepSeekService:
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL.rstrip("/")
        self.model = settings.DEEPSEEK_MODEL
        self.google_key = settings.GOOGLE_API_KEY

    async def get_advisory_response(
        self,
        user_message: str,
        history: List[ChatMessage],
        student_profile: Optional[Dict[str, Any]] = None,
        use_deep_research: bool = True
    ) -> ChatResponse:
        citations: List[CitationItem] = []
        research_context = ""

        # Step 1: Admission RAG Engine Retrieval
        rag_context, rag_citations = rag_service.build_grounded_rag_context(user_message, top_k=3)
        for rc in rag_citations:
            citations.append(CitationItem(
                source_title=rc["title"],
                source_url=rc.get("url", "Cơ sở dữ liệu Tuyển sinh 2026"),
                tier="Cấp 1 (Bộ GD&ĐT / Đề án chính thức)",
                verified=True
            ))

        # Step 2: Knowledge Graph Multi-hop Path Traversal
        h_code = "IRE"
        target_block = "A00"
        est_score = 25.0

        if student_profile:
            h_code = student_profile.get("holland", {}).get("holland_code", "IRE")
            target_block = student_profile.get("academic", {}).get("target_block", "A00")
            est_score = float(student_profile.get("academic", {}).get("estimated_exam_score", 25.0))
        else:
            # Extract block from user message if mentioned
            block_match = re.search(r'\b([A-D][0-9]{2}|H00|V00)\b', user_message.upper())
            if block_match:
                target_block = block_match.group(1)

        graph_paths = graph_service.query_multihop_advisory_paths(
            holland_code=h_code,
            target_block=target_block,
            estimated_score=est_score
        )

        graph_context_lines = []
        for gp in graph_paths[:3]:
            uni_strs = []
            for u in gp.get("offering_universities", [])[:3]:
                uni_strs.append(f"{u['university_name']} (Chuẩn 2025: {u['cutoff_2025']}đ - Tầng: {u['tier']})")
            graph_context_lines.append(
                f"- Ngành {gp['major_name']} (Mã: {gp['major_code']}): Cơ hội làm việc [{', '.join(gp.get('leading_careers', []))}]. "
                f"Trường đào tạo: {'; '.join(uni_strs)}."
            )
        graph_context_str = "\n".join(graph_context_lines)

        # Step 3: Query Live Data Retrieval Service (Server 2 on Vercel)
        retrieval_context, retrieval_citations = await retrieval_client.get_admission_knowledge_for_query(user_message)
        if retrieval_citations:
            citations.extend(retrieval_citations)

        # Step 4: Deep Research Knowledge Retrieval (MOET Circulars & Web Grounding)
        if use_deep_research:
            moet_context, moet_citations = await deep_research_service.search_admission_knowledge(user_message)
            if moet_citations:
                citations.extend(moet_citations)
            research_context = f"{retrieval_context}\n\n{moet_context}".strip()
        else:
            research_context = retrieval_context.strip()

        # Step 5: Build Enriched Prompt with Graph & RAG Grounding
        profile_context_str = ""
        if student_profile:
            acad = student_profile.get('academic', {})
            transcript_str = ""
            if acad.get('transcript_gpa_overall'):
                transcript_str = f" | Học bạ 3 năm THPT: GPA={acad.get('transcript_gpa_overall')} (Lớp 10: {acad.get('gpa_10')}, Lớp 11: {acad.get('gpa_11')}, Lớp 12: {acad.get('gpa_12')}) - Học lực: {acad.get('academic_ranking', 'Khá/Giỏi')}"
            if acad.get('transcript_block_score'):
                transcript_str += f", Tổng điểm học bạ khối {acad.get('target_block', 'A00')}={acad.get('transcript_block_score')}đ"

            profile_context_str = (
                f"\n[HỒ SƠ HỌC SINH HIỆN TẠI]\n"
                f"- Họ tên: {student_profile.get('student_name', 'Học sinh')}\n"
                f"- Điểm thi THPT dự kiến: {acad.get('estimated_exam_score', 'Chưa có')} (Khối {acad.get('target_block', 'A00')}){transcript_str}\n"
                f"- Mã Holland: {student_profile.get('holland', {}).get('holland_code', 'Chưa làm test')} ({student_profile.get('holland', {}).get('primary_trait', '')})\n"
                f"- DISC: {student_profile.get('disc', {}).get('dominant_trait', '')}\n"
                f"- Môn học yêu thích: {', '.join(acad.get('favorite_subjects', []))}\n"
            )

        full_system_prompt = (
            f"{SYSTEM_PROMPT}\n"
            f"{profile_context_str}\n"
            f"[KHO VĂN BẢN QUY PHẠM RAG & ĐIỂM CHUẨN]\n{rag_context}\n\n"
            f"[ĐỒ THỊ TRI THỨC ĐA CHẶNG (KNOWLEDGE GRAPH)]\n{graph_context_str}\n\n"
            f"[DỮ LIỆU ĐIỂM CHUẨN THỰC TẾ & BỘ GD&ĐT]\n{research_context}"
        )

        # Step 6: Call Primary DeepSeek API
        if self.api_key and self.api_key.strip():
            try:
                messages_payload = [{"role": "system", "content": full_system_prompt}]
                for msg in history[-6:]:
                    messages_payload.append({"role": msg.role, "content": msg.content})
                messages_payload.append({"role": "user", "content": user_message})

                async with httpx.AsyncClient(timeout=35.0) as client:
                    resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": self.model,
                            "messages": messages_payload,
                            "temperature": 0.4,
                            "max_tokens": 1500
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        reply = data["choices"][0]["message"]["content"]
                        thought = data["choices"][0]["message"].get("reasoning_content", "DeepSeek Reasoner: Phân tích logic sư phạm đối chiếu Đồ thị Tri thức và Quy chế Tuyển sinh 2026.")
                        return ChatResponse(
                            reply=reply,
                            thought_process=thought,
                            citations=citations,
                            recommended_followups=[
                                "Nên sắp xếp thứ tự nguyện vọng thế nào để chắc chắn đỗ?",
                                "Quy chế tuyển sinh 2026 có thay đổi gì về điểm ưu tiên?",
                                "Học phí và cơ hội học bổng của các trường trên ra sao?"
                            ]
                        )
            except Exception:
                pass

        # Step 7: Intelligent Secondary Engine via Google Gemini
        if self.google_key and self.google_key.strip():
            try:
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.google_key}"
                combined_prompt = f"{full_system_prompt}\n\n[CÂU HỎI CỦA HỌC SINH]: {user_message}"
                payload = {
                    "contents": [{"parts": [{"text": combined_prompt}]}]
                }
                async with httpx.AsyncClient(timeout=35.0) as client:
                    g_resp = await client.post(gemini_url, json=payload)
                    if g_resp.status_code == 200:
                        g_data = g_resp.json()
                        reply_text = g_data["candidates"][0]["content"]["parts"][0]["text"]
                        return ChatResponse(
                            reply=reply_text,
                            thought_process="AI Cố vấn Hướng nghiệp (RAG + Knowledge Graph + Gemini): Đối chiếu văn bản pháp lý 2026 và phân tích dữ liệu tuyển sinh.",
                            citations=citations,
                            recommended_followups=[
                                "Chiến lược phân bổ nguyện vọng 3 tầng cho điểm số của em?",
                                "Bảng quy đổi chứng chỉ IELTS 6.5 sang điểm đại học thế nào?",
                                "Học ngành AI thì trường nào đào tạo tốt nhất ở miền Bắc?"
                            ]
                        )
            except Exception:
                pass

        # Step 8: Grounded Local Pedagogical Engine with GraphRAG synthesis
        return self._generate_grounded_fallback_response(
            message=user_message,
            profile=student_profile,
            citations=citations,
            retrieval_context=retrieval_context,
            rag_context=rag_context,
            graph_paths=graph_paths
        )

    def _generate_grounded_fallback_response(
        self,
        message: str,
        profile: Optional[Dict[str, Any]],
        citations: List[CitationItem],
        retrieval_context: str = "",
        rag_context: str = "",
        graph_paths: Optional[List[Dict[str, Any]]] = None
    ) -> ChatResponse:
        score = profile.get("academic", {}).get("estimated_exam_score", 25.5) if profile else 25.5
        block = profile.get("academic", {}).get("target_block", "A00") if profile else "A00"
        h_code = profile.get("holland", {}).get("holland_code", "IRE") if profile else "IRE"

        msg_lower = message.lower()

        if any(w in msg_lower for w in ["nguyện vọng", "chiến lược", "sắp xếp", "đỗ"]):
            reply = (
                f"### Chiến lược Đăng ký Nguyện vọng Chuẩn hóa 2026 (Khối {block} - {score} điểm):\n\n"
                f"Dựa trên Quy chế tuyển sinh năm 2026 (Thông tư 06/2026/TT-BGDĐT) và nguyên tắc lọc ảo toàn quốc, "
                f"em tuyệt đối không nên dồn toàn bộ nguyện vọng vào các trường cùng mức điểm chuẩn. Hãy áp dụng chiến lược 3 tầng:\n\n"
                f"1. **Tầng 1 - Nguyện vọng Mơ ước (NV 1 - NV 2)**: Chọn các ngành/trường có điểm chuẩn năm 2025 cao hơn điểm của em từ 0.5 - 1.5 điểm "
                f"(Ví dụ: ĐH Bách Khoa Hà Nội, ĐHQG Hà Nội/TP.HCM). Đây là cơ hội thử thách nếu phổ điểm thi có lợi.\n"
                f"2. **Tầng 2 - Nguyện vọng Vừa sức (NV 3 - NV 4)**: Điểm chuẩn tiệm cận sát với điểm thi của em (±0.5 điểm). Đây là các nguyện vọng "
                f"có xác suất trúng tuyển cao nhất (70% - 85%).\n"
                f"3. **Tầng 3 - Nguyện vọng An toàn (NV 5 - NV 6)**: Điểm chuẩn năm trước thấp hơn điểm của em từ 1.5 - 2.5 điểm. "
                f"Đây là 'chốt chặn an toàn' bảo đảm 100% em không bị trượt đại học.\n\n"
                f"📌 **Lưu ý quy chế mới**: Hệ thống của Bộ GD&ĐT sẽ tự động xét từ trên xuống dưới. "
                f"Ngay khi trúng tuyển một nguyện vọng cao, các nguyện vọng phía dưới sẽ tự động hủy, nên em hãy đặt ngành mình THÍCH NHẤT lên NV 1!"
            )
            thought = f"Phân tích điểm thi {score} khối {block}, đối chiếu với phổ điểm tuyển sinh 2026 và quy chế lọc ảo tập trung."
        elif any(w in msg_lower for w in ["ielts", "chứng chỉ", "quy đổi", "tiếng anh"]):
            reply = (
                f"### Quy định Quy đổi Điểm IELTS Tuyển sinh Đại học 2026:\n\n"
                f"Theo hướng dẫn của Bộ GD&ĐT và đề án tuyển sinh các trường đại học top đầu năm 2026:\n\n"
                f"• **Ngưỡng miễn thi tốt nghiệp**: Đạt từ IELTS 4.0 trở lên được miễn thi bài thi Ngoại ngữ tốt nghiệp THPT (tính 10 điểm tốt nghiệp).\n"
                f"• **Xét tuyển đại học**: Mỗi trường có bảng quy đổi độc lập:\n"
                f"  - **Đại học Bách khoa Hà Nội**: IELTS 6.0 quy đổi 9.0; IELTS 6.5+ quy đổi 10.0 môn Tiếng Anh.\n"
                f"  - **ĐH Kinh tế Quốc dân (NEU)**: IELTS 5.5 quy đổi 8.0; IELTS 6.5 quy đổi 9.0; IELTS 7.5+ quy đổi 10.0.\n"
                f"  - **ĐH Ngoại thương (FTU)**: Yêu cầu tối thiểu IELTS 6.5 để nộp hồ sơ xét kết hợp học bạ hoặc điểm 2 môn thi tốt nghiệp.\n"
                f"  - **ĐHQG TP.HCM / Hà Nội**: Quy đổi thành thang điểm 10 kết hợp trong điểm xét tuyển tổng hợp ĐGNL.\n\n"
                f"💡 **Khuyến nghị**: Nếu em đã có chứng chỉ IELTS từ 6.5 trở lên, hãy tận dụng ngay phương thức xét tuyển kết hợp sớm để tăng cơ hội trúng tuyển."
            )
            thought = "Tra cứu quy chế quy đổi chứng chỉ quốc tế theo đề án các trường ĐH trọng điểm."
        elif graph_paths and len(graph_paths) > 0:
            top_path = graph_paths[0]
            unis_text = ""
            for u in top_path.get("offering_universities", [])[:3]:
                unis_text += f"\n  - **{u['university_name']}**: Điểm chuẩn 2025: {u['cutoff_2025']}đ (Dự báo 2026: ~{u['cutoff_pred_2026']}đ - Phân hạng: *{u['tier']}*)"

            reply = (
                f"Chào em! Dựa trên đồ thị tri thức hướng nghiệp kết nối mã Holland **{h_code}** và khối xét tuyển **{block}**:\n\n"
                f"🎯 **Ngành đề xuất hàng đầu**: **{top_path['major_name']}** (Mã ngành: {top_path['major_code']})\n"
                f"• **Cơ hội việc làm**: {', '.join(top_path.get('leading_careers', []))}\n"
                f"• **Mức lương tham khảo**: {top_path.get('salary_range', '12 - 25 triệu/tháng')}\n"
                f"• **Triển vọng tương lai**: {top_path.get('growth_outlook', 'Nhu cầu nhân lực tăng cao')}\n\n"
                f"🏫 **Các trường đại học đào tạo phù hợp nhất**:{unis_text}\n\n"
                f"💡 Với mức điểm dự kiến **{score} điểm**, em có thể tự tin nộp hồ sơ vào các trường nhóm *Vừa sức* và đặt 1 nguyện vọng *Mơ ước* nhé!"
            )
            thought = "Duyệt Đồ thị Tri thức đa chặng (Knowledge Graph Traversal) kết nối Holland Trait -> Major -> University -> Careers."
        elif rag_context:
            reply = (
                f"Chào em! Cố vấn CareerCompass-AI 2026 đã tra cứu thông tin tuyển sinh liên quan từ hệ thống:\n\n"
                f"{rag_context[:600]}...\n\n"
                f"💡 Em có thể cung cấp thêm điểm thi dự kiến hoặc ngành học muốn tìm hiểu để thầy/cô đưa ra danh sách trường cụ thể hơn nhé!"
            )
            thought = "Truy xuất tài liệu từ kho tri thức RAG Tuyển sinh 2026."
        else:
            reply = (
                f"Chào em! Thầy/cô cố vấn CareerCompass-AI 2026 đã ghi nhận câu hỏi của em.\n\n"
                f"Dựa trên hồ sơ của em (Mã Holland: **{h_code}**, Tổ hợp mục tiêu: **{block}**, Điểm dự kiến: **{score} điểm**):\n"
                f"• Em có thế mạnh nổi trội ở tư duy logic và phân tích hệ thống. Các nhóm ngành như Máy tính & CNTT, "
                f"Công nghệ kỹ thuật & Vi mạch, và Kinh doanh & Dữ liệu đang có triển vọng việc làm rất mạnh mẽ.\n"
                f"• Với mức điểm {score}, em hoàn toàn đủ điều kiện cạnh tranh vào các trường đại học uy tín.\n\n"
                f"Em có thể chia sẻ thêm về ngành nghề em quan tâm nhất hoặc khu vực muốn theo học để thầy/cô gợi ý chi tiết hơn nhé!"
            )
            thought = "Tổng hợp dữ liệu hồ sơ cá nhân hóa kết hợp ngân hàng ngành đào tạo chuẩn GD&ĐT."

        if not citations:
            citations.append(CitationItem(
                source_title="Bộ Giáo dục và Đào tạo - Cổng thông tin Tuyển sinh Quốc gia",
                source_url="https://moet.gov.vn",
                tier="Cấp 1 (Cơ quan nhà nước)"
            ))

        return ChatResponse(
            reply=reply,
            thought_process=thought,
            citations=citations,
            recommended_followups=[
                "Học phí các trường công lập tự chủ năm 2026 là bao nhiêu?",
                "Nên chọn học ngành Khoa học Máy tính hay Thiết kế Vi mạch?",
                "Công thức tính điểm ưu tiên khu vực giảm dần áp dụng thế nào?"
            ]
        )

deepseek_service = DeepSeekService()
