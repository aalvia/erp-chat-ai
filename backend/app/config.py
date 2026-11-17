from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    jwt_secret: str
    jwt_expire_minutes: int = 480
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:1.5b"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_num_ctx: int = 2048
    ollama_keep_alive: str = "10m"
    cors_origins: str = "http://localhost:5173"
    tax_rate: Decimal = Decimal("0")
    currency: str = "USD"
    low_stock_threshold: int = 10

    @field_validator("ollama_base_url")
    @classmethod
    def strip_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def knowledge_dir(self) -> Path:
        return ROOT_DIR / "data" / "knowledge"

    @property
    def chroma_dir(self) -> Path:
        return ROOT_DIR / "data" / "chroma_db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
