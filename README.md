# CareerCompass-AI - Unified AI Career Advisory & Admissions API Platform 2026

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Vercel Deployment](https://img.shields.io/badge/Vercel-Production%20Live-black.svg)](https://careercompass-ai-api.vercel.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Nền tảng Hợp nhất Cố vấn Hướng nghiệp Cá nhân hóa & Truy xuất Dữ liệu Tuyển sinh Đại học Việt Nam 2026 (Single Unified Backend Platform)**.
Tuân thủ đầy đủ **Thông tư 06/2026/TT-BGDĐT** của Bộ Giáo dục & Đào tạo và **Nghị định 13/2023/NĐ-CP** về bảo vệ dữ liệu cá nhân.

- 🌐 **Production URL**: [https://careercompass-ai-api.vercel.app](https://careercompass-ai-api.vercel.app)
- 📖 **Swagger UI Docs**: [https://careercompass-ai-api.vercel.app/docs](https://careercompass-ai-api.vercel.app/docs)
- 📑 **ReDoc**: [https://careercompass-ai-api.vercel.app/redoc](https://careercompass-ai-api.vercel.app/redoc)

---

## 🏗️ 1. Kiến Trúc Hợp Nhất (Single Unified Platform)

Hệ thống đã được tái cấu trúc từ 2 microservice riêng rẽ thành **1 API duy nhất tinh gọn**, loại bỏ hoàn toàn độ trễ mạng và rủi ro timeout giữa các server:

```
careercompass-api/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── survey.py          # Khảo sát đa chiều (84Q Holland Sông An, SCCT, Gardner, DISC)
│   │       │   ├── profile.py         # Hồ sơ Career Passport & Xuất báo cáo
│   │       │   ├── recommendations.py # Phân bổ nguyện vọng 3 tầng (Mơ ước, Vừa sức, An toàn)
│   │       │   ├── regulations.py     # Quy chế 2026, điểm ưu tiên giảm dần, quy đổi IELTS
│   │       │   ├── roadmap.py         # Lộ trình tuyển sinh 6 chặng lớp 12
│   │       │   ├── chat.py            # Trợ lý AI DeepSeek Reasoner + Gemini fallback
│   │       │   ├── users.py           # Quản lý học sinh, điểm học bạ, bookmark nguyện vọng
│   │       │   ├── graph.py           # Đồ thị tri thức (Knowledge Graph multi-hop)
│   │       │   ├── rag.py             # Tra cứu văn bản quy chế & đề án chính thức
│   │       │   ├── retrieval.py       # Tra cứu điểm chuẩn & kích hoạt crawler
│   │       │   └── universities.py    # Danh mục cơ sở đào tạo, học phí, chỉ tiêu
│   │       └── router.py              # Đăng ký 41 Endpoints RESTful
│   ├── core/
│   │   └── config.py                  # Pydantic Settings & Environment Variables
│   ├── crawler/                       # Engine cào dữ liệu Tuyensinh247 & VietnamNet
│   │   ├── base.py                    # BaseCrawler (Rate limit, checkpoint, Decree 13/2023)
│   │   ├── tuyensinh247.py            # Cào điểm chuẩn, mã ngành, chỉ tiêu
│   │   ├── vietnamnet.py              # Cào phổ điểm thi THPT (ẩn danh hóa)
│   │   └── gemini_extractor.py        # Gemini 2.5 Flash trích xuất HTML phi cấu trúc
│   ├── data/                          # Cơ sở dữ liệu JSON đã cấu trúc sẵn
│   │   ├── holland_questions.json     # 84 câu hỏi authentic Hướng nghiệp Sông An
│   │   ├── gardner_questions.json     # Đa trí tuệ Gardner
│   │   ├── disc_questions.json        # Trắc nghiệm tính cách DISC
│   │   ├── scct_questions.json        # Thang đo tự đánh giá năng lực SCCT
│   │   ├── universities_database.json # Cơ sở đào tạo đại học toàn quốc
│   │   ├── majors_database.json       # 23 nhóm ngành chuẩn GD&ĐT
│   │   ├── regulations_2026.json      # Thông tư 06/2026/TT-BGDĐT
│   │   └── roadmap_milestones.json    # Mốc thời gian thi tốt nghiệp & xét tuyển
│   ├── db/
│   │   └── supabase_client.py         # Database Client (asyncpg, Supabase & local fallback)
│   ├── schemas/                       # Pydantic Schemas V2
│   ├── services/                      # Nghiệp vụ lõi (Graph, RAG, In-Process Retrieval)
│   ├── tasks/                         # Scheduler định kỳ
│   └── main.py                        # FastAPI Application Entrypoint
├── data/                              # Ngân hàng 333 câu hỏi Sông An nguyên bản
├── docs/                              # Tài liệu kỹ năng & đặc tả nghiệp vụ
├── scripts/                           # Script migration và seed dữ liệu
├── supabase_schema.sql                # 16 bảng PostgreSQL chuẩn hóa
├── requirements.txt                   # Danh mục dependencies
├── vercel.json                        # Cấu hình deploy serverless Vercel
├── .env.example                       # Mẫu biến môi trường
└── README.md
```

---

## ⚡ 2. Các Phân Hệ Tính Năng Chính

### A. Khảo Sát Đa Chiều & Hồ Sơ Hướng Nghiệp (Career Passport)
- **Holland RIASEC**: Ngân hàng 84 câu hỏi chuẩn hóa bởi Doanh nghiệp Xã hội Hướng nghiệp Sông An.
- **SCCT (Social Cognitive Career Theory)**: Ma trận 4 góc phần tư đối chiếu Hứng thú vs. Niềm tin Năng lực (Hành động, Rèn luyện, Dự phòng, Hạn chế).
- **Đa trí tuệ Gardner & DISC**: Nhận diện thế mạnh bẩm sinh và phong cách làm việc.
- **Tính toán Điểm Học Bạ**: GPA 10, 11, 12, tổng điểm tổ hợp môn, chứng chỉ IELTS và điểm ưu tiên khu vực.

### B. Đồ Thị Tri Thức Đa Chặng (Knowledge Graph / GraphRAG)
- Mạng lưới **153 Đỉnh (Nodes)** và **298 Cạnh (Edges)**.
- Traversal đa chặng: `Mã Holland -> Ngành phù hợp -> Khối thi -> Trường ĐH đào tạo -> Cơ hội việc làm đầu ra`.
- Tự động phân tầng: **Mơ ước (Dream)**, **Vừa sức (Target)**, **An toàn (Safety)**.

### C. Admission RAG Engine (Truy Xuất Quy Chế & Điểm Chuẩn)
- Cơ chế Hybrid Search (Semantic + TF-IDF) tra cứu trực tiếp toàn văn Thông tư 06/2026/TT-BGDĐT.
- Trích dẫn minh bạch nguồn gốc (Citations), chống ảo giác (Anti-hallucination) cho AI.

### D. Hệ Thống Cào & Truy Xuất Điểm Chuẩn In-Process
- Tích hợp nội bộ với thời gian phản hồi < 1ms.
- Điểm chuẩn các trường đại học, dự báo điểm chuẩn 2026 bằng mô hình hồi quy.

---

## 🚀 3. Hướng Dẫn Khởi Chạy Local

### Cài đặt môi trường
```bash
git clone https://github.com/TechFutureAIFPT/careercompass-api.git
cd careercompass-api

# Tạo môi trường ảo
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate # Linux/Mac

# Cài đặt dependencies
pip install -r requirements.txt
```

### Cấu hình biến môi trường
Tạo file `.env` từ `.env.example`:
```bash
copy .env.example .env
```
Điền các API keys cần thiết (`DEEPSEEK_API_KEY`, `GOOGLE_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`).

### Khởi chạy Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Truy cập tài liệu API: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📦 4. Kiểm Thử Hệ Thống (Automated Testing)
Chạy test suite kiểm tra toàn diện 10 phân hệ:
```bash
python -u scratch/test_unified_api.py
```

---

## 📜 5. Bản Quyền & Giấy Phép
- Dữ liệu câu hỏi trắc nghiệm nghề nghiệp được chuẩn hóa từ Doanh nghiệp Xã hội Hướng nghiệp Sông An theo giấy phép Creative Commons **CC BY-ND 4.0**.
- Mã nguồn nền tảng phát hành theo giấy phép **MIT License**.
