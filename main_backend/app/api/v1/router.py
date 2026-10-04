from fastapi import APIRouter
from app.api.v1.endpoints import (
    survey,
    profile,
    recommendations,
    regulations,
    roadmap,
    chat,
    users,
    graph,
    rag,
    retrieval,
    universities
)

api_router = APIRouter()

api_router.include_router(survey.router, prefix="/surveys", tags=["Khảo sát Đa chiều (RIASEC / SCCT / Gardner / DISC)"])
api_router.include_router(profile.router, prefix="/profiles", tags=["Hồ sơ Hướng nghiệp Cá nhân (Career Passport)"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Tư vấn Nguyện vọng & Ma trận So sánh"])
api_router.include_router(regulations.router, prefix="/regulations", tags=["Quy chế Tuyển sinh 2026 & Quy đổi Điểm"])
api_router.include_router(roadmap.router, prefix="/roadmap", tags=["Lộ trình Tuyển sinh Lớp 12"])
api_router.include_router(chat.router, prefix="/chat", tags=["Trợ lý Hướng nghiệp AI (DeepSeek Reasoner)"])
api_router.include_router(users.router, prefix="/users", tags=["Quản lý Học sinh & Lưu trữ Dữ liệu (User Persistence)"])
api_router.include_router(graph.router, prefix="/graph", tags=["Đồ thị Tri thức Hướng nghiệp (Knowledge Graph)"])
api_router.include_router(rag.router, prefix="/rag", tags=["Cơ chế Tra cứu RAG Tuyển sinh (Admission RAG Engine)"])
api_router.include_router(retrieval.router, prefix="/retrieval", tags=["Truy xuất Dữ liệu Tuyển sinh & Điểm chuẩn (Admission Data Retrieval)"])
api_router.include_router(universities.router, prefix="/universities", tags=["Cơ sở Đào tạo & Điểm chuẩn Đại học"])
