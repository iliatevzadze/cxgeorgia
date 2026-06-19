"""Application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, computed_field
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

    auth_secret_key: str = "change-me-local-development-secret"
    auth_algorithm: str = "HS256"
    auth_access_token_expire_minutes: int = 30

    default_first_response_minutes: int = 60
    default_resolution_minutes: int = 1440

    storage_endpoint: str = Field(
        default="http://localhost:9000",
        validation_alias=AliasChoices("STORAGE_ENDPOINT", "MINIO_ENDPOINT"),
    )
    storage_access_key: str = Field(
        default="minio_local_user",
        validation_alias=AliasChoices("STORAGE_ACCESS_KEY", "MINIO_ROOT_USER"),
    )
    storage_secret_key: str = Field(
        default="change_me_local_only",
        validation_alias=AliasChoices("STORAGE_SECRET_KEY", "MINIO_ROOT_PASSWORD"),
    )
    storage_bucket_default: str = Field(
        default="georgian-cx-local",
        validation_alias=AliasChoices("STORAGE_BUCKET_DEFAULT", "MINIO_BUCKET_NAME"),
    )

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
