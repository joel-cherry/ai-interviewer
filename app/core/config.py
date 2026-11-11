from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Mock Interviewer API"
    app_env: Literal["development", "testing", "production"] = "testing"
    debug: bool = True
    project_version: str = "0.1.0"
    api_v1_str: str = "/api/v1"
    llm_provider: Literal["mock", "openai"] = "mock"

    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    postgres_db: str = "ai_interviewer"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "db"
    postgres_port: int = 5432
    database_url: str = "sqlite+aiosqlite:///./test.db"

    log_level: str = "INFO"
    log_format: Literal["json", "plain"] = "json"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def ensure_database_url(self) -> "Settings":
        use_sqlite_for_local_tests = self.app_env == "testing" and (
            not self.database_url or self.database_url.startswith("postgresql")
        )
        if use_sqlite_for_local_tests:
            self.database_url = "sqlite+aiosqlite:///./test.db"
        elif not self.database_url or self.database_url == "postgresql+asyncpg://postgres:postgres@db:5432/ai_interviewer":
            self.database_url = (
                f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@"
                f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return self

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_testing(self) -> bool:
        return self.app_env == "testing"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
