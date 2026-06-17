"""Worker configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Minimal worker settings (Phase 0 skeleton)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"
    app_name: str = "Georgian CX Platform"
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_host_port: int = 16379
    redis_db: int = 0
    worker_redis_mode: str = "local"

    @property
    def redis_broker_url_local(self) -> str:
        """Redis URL for worker running on the host machine."""
        return f"redis://localhost:{self.redis_host_port}/{self.redis_db}"

    @property
    def redis_broker_url_docker(self) -> str:
        """Redis URL for worker running inside Docker Compose network."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def redis_broker_url(self) -> str:
        """Active Redis URL based on WORKER_REDIS_MODE."""
        if self.worker_redis_mode == "docker":
            return self.redis_broker_url_docker
        return self.redis_broker_url_local


@lru_cache
def get_settings() -> Settings:
    return Settings()
