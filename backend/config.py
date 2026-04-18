"""
HealthVault AI — Application Configuration
Centralized settings loaded from environment variables.
"""
from functools import lru_cache
from typing import List, Literal

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_NAME: str = "HealthVault AI"
    APP_VERSION: str = "1.0.0"
    SECRET_KEY: str = "change-me-in-production"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8081"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str = ""
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── Supabase ─────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # ── Storage ───────────────────────────────────────────────
    STORAGE_PROVIDER: Literal["supabase", "s3"] = "supabase"
    SUPABASE_BUCKET_REPORTS: str = "health-reports"
    SUPABASE_BUCKET_PRESCRIPTIONS: str = "prescriptions"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_REGION: str = "us-east-1"

    # ── AI ────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    GEMINI_API_KEY: str = ""
    AI_PROVIDER: Literal["openai", "gemini"] = "openai"

    # ── OCR ───────────────────────────────────────────────────
    TESSERACT_CMD: str = "/usr/bin/tesseract"

    # ── Twilio / WhatsApp ────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = "whatsapp:+14155238886"

    # ── Redis ─────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Logging ───────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ── Upload limits ─────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/tiff",
    ]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
