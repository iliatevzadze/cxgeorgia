"""Tests for database configuration."""

import pytest

from app.core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_database_url_local_mode_explicit() -> None:
    settings = Settings(
        backend_database_mode="local",
        backend_database_url_local=(
            "postgresql+asyncpg://user:pass@localhost:15432/cx_platform"
        ),
    )
    assert settings.database_url == (
        "postgresql+asyncpg://user:pass@localhost:15432/cx_platform"
    )
    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_database_url_docker_mode_explicit() -> None:
    settings = Settings(
        backend_database_mode="docker",
        backend_database_url_docker=(
            "postgresql+asyncpg://user:pass@postgres:5432/cx_platform"
        ),
    )
    assert settings.database_url == (
        "postgresql+asyncpg://user:pass@postgres:5432/cx_platform"
    )
    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_database_url_local_mode_from_postgres_components() -> None:
    settings = Settings(
        backend_database_mode="local",
        backend_database_url_local=None,
        postgres_user="cx_user",
        postgres_password="cx_password",
        postgres_host_port=15432,
        postgres_db="cx_platform",
    )
    assert settings.database_url == (
        "postgresql+asyncpg://cx_user:cx_password@localhost:15432/cx_platform"
    )


def test_database_url_docker_mode_from_postgres_components() -> None:
    settings = Settings(
        backend_database_mode="docker",
        backend_database_url_docker=None,
        postgres_user="cx_user",
        postgres_password="cx_password",
        postgres_host="postgres",
        postgres_port=5432,
        postgres_db="cx_platform",
    )
    assert settings.database_url == (
        "postgresql+asyncpg://cx_user:cx_password@postgres:5432/cx_platform"
    )


def test_default_database_mode_is_local() -> None:
    assert Settings.model_fields["backend_database_mode"].default == "local"
