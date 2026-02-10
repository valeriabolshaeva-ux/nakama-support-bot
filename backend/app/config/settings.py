"""Application settings using Pydantic."""

from typing import List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""
    
    # === Telegram Bot ===
    bot_token: str = Field(
        ...,
        description="Telegram Bot Token from @BotFather"
    )
    support_chat_id: int = Field(
        ...,
        description="Support Group chat ID (with topics enabled)"
    )
    operators: list[int] = Field(
        default_factory=list,
        description="List of operator Telegram user IDs"
    )
    
    # === Application ===
    timezone: str = Field(
        default="Europe/Madrid",
        description="Application timezone"
    )
    db_path: str = Field(
        default="./data/support.sqlite",
        description="Path to SQLite database file"
    )
    log_level: str = Field(
        default="info",
        description="Logging level (debug, info, warning, error)"
    )
    healthcheck_port: Optional[int] = Field(
        default=None,
        description="Port for HTTP healthcheck (e.g. PORT on Railway). If set, GET / returns 200.",
        validation_alias="PORT",
    )
    
    # === Working Hours ===
    work_hours_start: int = Field(
        default=10,
        description="Start of working hours (24h format)"
    )
    work_hours_end: int = Field(
        default=19,
        description="End of working hours (24h format)"
    )
    work_days: list[int] = Field(
        default=[1, 2, 3, 4, 5],
        description="Working days (1=Monday, 7=Sunday)"
    )
    
    @field_validator("operators", mode="before")
    @classmethod
    def parse_operators(cls, v: Union[str, List[int]]) -> List[int]:
        """Parse operators from comma-separated string."""
        if isinstance(v, str):
            if not v.strip():
                return []
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v
    
    @field_validator("work_days", mode="before")
    @classmethod
    def parse_work_days(cls, v: Union[str, List[int]]) -> List[int]:
        """Parse work days from comma-separated string."""
        if isinstance(v, str):
            if not v.strip():
                return [1, 2, 3, 4, 5]
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton settings instance
settings = Settings()
