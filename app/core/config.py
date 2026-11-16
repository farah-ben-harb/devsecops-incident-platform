from functools import lru_cache

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DevSecOps Incident Platform"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    default_page_size: int = 20
    incident_api_token: SecretStr | None = None
    database_url: str = (
        "postgresql+psycopg://incident_user:change_me@localhost:5432/incident_db"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def require_production_api_token(self) -> "Settings":
        if self.app_env.lower() in {"prod", "production"}:
            token = self.incident_api_token.get_secret_value() if self.incident_api_token else ""
            if len(token) < 32 or token.startswith("local-development-"):
                raise ValueError("A unique INCIDENT_API_TOKEN of at least 32 characters is required")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
