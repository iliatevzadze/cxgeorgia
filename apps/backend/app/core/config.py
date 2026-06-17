"""Application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

DatabaseMode = Literal["local", "docker"]


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"
    app_name: str = "Georgian CX Platform"
    backend_port: int = 8000
    default_locale: str = "ka"
    supported_locales: str = "ka,en"

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_host_port: int = 15432
    postgres_db: str = "georgian_cx_platform"
    postgres_user: str = "georgian_cx_user"
    postgres_password: str = "change_me_local_only"

    backend_database_mode: DatabaseMode = "local"
    backend_database_url_local: str | None = None
    backend_database_url_docker: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Resolved async SQLAlchemy database URL for the active mode."""
        if self.backend_database_mode == "docker":
            if self.backend_database_url_docker:
                return self.backend_database_url_docker
            return (
                f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )

        if self.backend_database_url_local:
            return self.backend_database_url_local

        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@localhost:{self.postgres_host_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
