"""
Application Configuration via Pydantic Settings.

All environment variables are validated at application startup.
If a required variable is missing, the application will NOT start.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """PostgreSQL connection settings."""
    
    model_config = SettingsConfigDict(env_prefix="PG__")
    
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    user: str = Field(default="postgres", description="Database user")
    password: str = Field(default="postgres", description="Database password")
    database: str = Field(default="app_db", description="Database name")
    
    @property
    def url(self) -> str:
        """Build database connection URL."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def sync_url(self) -> str:
        """Build synchronous database connection URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisSettings(BaseSettings):
    """Redis connection settings."""
    
    model_config = SettingsConfigDict(env_prefix="REDIS__")
    
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    password: str | None = Field(default=None, description="Redis password")
    
    @property
    def url(self) -> str:
        """Build Redis connection URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class OpenAISettings(BaseSettings):
    """OpenAI API settings."""
    
    model_config = SettingsConfigDict(env_prefix="OPENAI__")
    
    api_key: str | None = Field(default=None, description="OpenAI API Key")
    url: str = Field(
        default="https://api.openai.com/v1/chat/completions",
        description="OpenAI API URL"
    )
    org_id: str | None = Field(default=None, description="OpenAI Organization ID")
    
    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str | None) -> str | None:
        """Validate OpenAI API key format."""
        if v and not v.startswith("sk-"):
            raise ValueError("OpenAI API key must start with 'sk-'")
        return v


class SMTPSettings(BaseSettings):
    """SMTP email settings."""
    
    model_config = SettingsConfigDict(env_prefix="SMTP__")
    
    host: str = Field(default="smtp.gmail.com", description="SMTP host")
    port: int = Field(default=587, description="SMTP port")
    user: str | None = Field(default=None, description="SMTP user")
    password: str | None = Field(default=None, description="SMTP password")


class SupabaseSettings(BaseSettings):
    """Supabase settings."""
    
    model_config = SettingsConfigDict(env_prefix="SUPABASE_")
    
    project_id: str | None = Field(default=None, description="Supabase project ID")
    url: str | None = Field(default=None, description="Supabase URL")
    publishable_key: str | None = Field(default=None, description="Supabase public key")
    secret_key: str | None = Field(default=None, description="Supabase secret key")


class Settings(BaseSettings):
    """Main application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )
    
    # --- Application ---
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="local", description="Environment: local/dev/staging/prod")
    app_name: str = Field(default="Customer Support API", description="Application name")
    
    # --- Security ---
    secret_key: str = Field(
        default="change-this-secret-key-in-production-minimum-32-chars",
        description="JWT secret key"
    )
    access_token_expire_minutes: int = Field(default=30, description="Access token expiry")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiry")
    
    # --- Nested Settings ---
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    smtp: SMTPSettings = Field(default_factory=SMTPSettings)
    supabase: SupabaseSettings = Field(default_factory=SupabaseSettings)


# Singleton — created once on import
settings = Settings()
