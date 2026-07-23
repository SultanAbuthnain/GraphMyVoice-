"""
app/config.py
─────────────
Centralised settings loaded from environment / .env file.
Uses pydantic-settings so every field is validated at startup.
"""

from functools import lru_cache
from pydantic import AnyUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────
    app_env: str = "development"
    app_debug: bool = True
    app_port: int = 8000

    # ── Database ─────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mindmap_db"

    # ── JWT ──────────────────────────────────
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 days

    # ── AI Providers ─────────────────────────────
    groq_api_key: str = ""

    # ── LLM / STT (Groq) ─────────────────────────
    llm_model: str = "llama-3.3-70b-versatile"
    llm_max_retries: int = 3
    llm_temperature: float = 0.1

    # ── Whisper ──────────────────────────────
    whisper_model: str = "whisper-1"
    whisper_language: str = "auto"
    audio_chunk_minutes: int = 10

    # ── File Upload ──────────────────────────
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 500
    max_audio_duration_minutes: int = 60
    allowed_audio_types: str = "audio/mpeg,audio/wav,audio/mp4,audio/ogg,audio/x-m4a"

    # ── Rate Limiting ─────────────────────────
    rate_limit_uploads_per_hour: int = 3

    # ── CORS ─────────────────────────────────
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # ── Guardrails ───────────────────────────
    min_transcript_words: int = 50
    hallucination_threshold: float = 0.70

    # ── Computed helpers ─────────────────────
    @property
    def allowed_audio_types_list(self) -> list[str]:
        return [t.strip() for t in self.allowed_audio_types.split(",")]

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance. Use as FastAPI dependency."""
    return Settings()
