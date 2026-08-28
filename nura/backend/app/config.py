"""Runtime configuration. Secrets stay on the server."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "nura-api"
    environment: str = "development"

    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "JBFqnCBsd6RMkjVDRZzb"
    elevenlabs_model_id: str = "eleven_flash_v2_5"
    elevenlabs_stt_model_id: str = "scribe_v2"

    ai_provider: Literal["gemini", "openai", "none"] = "gemini"
    ai_api_key: str = ""
    ai_model: str = ""

    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    max_image_bytes: int = 8 * 1024 * 1024
    max_audio_bytes: int = 10 * 1024 * 1024
    max_image_dimension: int = 1600
    rate_limit_per_minute: int = 40

    session_ttl_seconds: int = 30 * 60

    @field_validator("ai_provider", mode="before")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        if not value:
            return "gemini"
        return str(value).strip().lower()

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [item.strip() for item in self.cors_origins.split(",") if item.strip()]
        if self.frontend_url and self.frontend_url not in origins:
            origins.append(self.frontend_url)
        return origins

    @property
    def resolved_ai_model(self) -> str:
        if self.ai_model:
            return self.ai_model
        if self.ai_provider == "openai":
            return "gpt-4o-mini"
        return "gemini-2.0-flash"

    @property
    def has_ai(self) -> bool:
        return bool(self.ai_api_key) and self.ai_provider != "none"

    @property
    def has_elevenlabs(self) -> bool:
        return bool(self.elevenlabs_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
