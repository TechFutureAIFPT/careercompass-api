from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title="CareerCompass-AI 2026 - Unified Career Advisory & Admissions Data Retrieval Platform",
    version="1.0.0",
    description="Nền tảng Hợp nhất Cố vấn Hướng nghiệp & Cào - Truy xuất Dữ liệu Tuyển sinh Đại học Việt Nam (DeepSeek Reasoner R1/V3 + Knowledge Graph + RAG + Thông tư 06/2026/TT-BGDĐT)",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Include Unified API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "CareerCompass-AI 2026 - Unified API Platform",
        "primary_ai": "DeepSeek Reasoner (R1 / V3)",
        "architecture": "Single Unified API (In-Process Data Retrieval & Crawler Integrated)",
        "regulation": "Thông tư 06/2026/TT-BGDĐT",
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "careercompass_unified_api",
        "ai_engine": "DeepSeek Reasoner (R1 / V3)",
        "architecture": "Single Unified Service",
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
