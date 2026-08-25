from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    anthropic_api_key: str = Field(default="sk-ant-placeholder")
    model_reasoning: str = "claude-sonnet-4-6"
    model_volume: str = "claude-haiku-4-5-20251001"
    reddit_client_id: str = Field(default="")
    reddit_client_secret: str = Field(default="")
    reddit_user_agent: str = Field(default="SignalHarvest/1.0")
    sentinel_max_signals_per_source: int = Field(default=50, ge=1, le=500)
    curator_min_score: int = Field(default=40, ge=0, le=100)
    database_path: str = Field(default="./data/signalharvest.db")
    digest_output_dir: str = Field(default="./output/digests")
    log_file: str = Field(default="./logs/signalharvest.log")
    scheduler_hour: int = Field(default=1, ge=0, le=23)
    scheduler_minute: int = Field(default=0, ge=0, le=59)
    log_level: str = Field(default="INFO")

    # Gateway
    signalharvest_api_key: str = Field(default="")
    allowed_origins: str = Field(default="")
    environment: str = Field(default="development")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return upper

    @property
    def database_path_obj(self) -> Path:
        return Path(self.database_path)

    @property
    def digest_output_path(self) -> Path:
        return Path(self.digest_output_dir)

    @property
    def log_file_path(self) -> Path:
        return Path(self.log_file)

    def ensure_dirs(self) -> None:
        for d in [
            self.database_path_obj.parent,
            self.digest_output_path,
            self.log_file_path.parent,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    @property
    def reddit_configured(self) -> bool:
        return bool(self.reddit_client_id and self.reddit_client_secret)

    @property
    def allowed_origins_list(self) -> list[str]:
        configured = [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
        if configured:
            return configured
        if self.environment != "production":
            return ["http://localhost:3000", "http://localhost:3200"]
        return []


settings = Settings()
