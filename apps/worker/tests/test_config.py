"""Tests for worker settings."""

from worker.core.config import Settings


def test_default_app_name() -> None:
    settings = Settings()
    assert settings.app_name == "Georgian CX Platform"


def test_default_environment() -> None:
    settings = Settings()
    assert settings.app_env == "local"


def test_local_redis_url_uses_localhost() -> None:
    settings = Settings()
    assert "localhost" in settings.redis_broker_url_local


def test_local_redis_url_uses_host_port() -> None:
    settings = Settings()
    assert "16379" in settings.redis_broker_url_local


def test_docker_redis_url_uses_service_name() -> None:
    settings = Settings()
    assert "redis" in settings.redis_broker_url_docker


def test_docker_redis_url_uses_container_port() -> None:
    settings = Settings()
    assert ":6379/" in settings.redis_broker_url_docker


def test_local_mode_uses_local_redis_url() -> None:
    settings = Settings(worker_redis_mode="local")
    assert settings.redis_broker_url == settings.redis_broker_url_local


def test_docker_mode_uses_docker_redis_url() -> None:
    settings = Settings(worker_redis_mode="docker")
    assert settings.redis_broker_url == settings.redis_broker_url_docker
