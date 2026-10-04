import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "CareerCompass-AI 2026 - AI Career & University Orientation API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "*"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            import json
            try:
                return json.loads(v)
            except Exception:
                return ["*"]
        return v

    # AI DeepSeek (Core Reasoner)
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # Microservice Server 2: Data Retrieval & Crawler (Gemini + Supabase)
    RETRIEVAL_SERVICE_URL: str = "https://admissions-data-retrieval-api.vercel.app"

    # Google API (Optional Deep Research Search Grounding)
    GOOGLE_API_KEY: str = ""
    GOOGLE_SEARCH_ENGINE_ID: str = ""

    # Supabase Database & Auth
    SUPABASE_URL: str = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or ""
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or ""
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
    DATABASE_URL: str = os.getenv("DATABASE_URL") or ""


    # Redis Cache (Optional, fallback to in-memory cache)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Crawler Settings (Compliance with Robots.txt & Decree 13/2023)
    CRAWLER_USER_AGENT: str = "CareerCompassBot/1.0 (+contact@careercompass2026.vn)"
    CRAWLER_DELAY_SECONDS: float = 1.5
    CRAWLER_MAX_WORKERS: int = 3
    CHECKPOINT_DIR: str = "/tmp/checkpoints" if os.getenv("VERCEL") else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "checkpoints")

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
