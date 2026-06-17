"""Tests for JWT access token utilities."""

from datetime import timedelta

import pytest
from jose import JWTError

from app.core.config import Settings, get_settings
from app.core.security import create_access_token, decode_access_token


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def auth_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-for-jwt")
    monkeypatch.setenv("AUTH_ALGORITHM", "HS256")
    monkeypatch.setenv("AUTH_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    get_settings.cache_clear()


def test_create_access_token_returns_string(auth_settings: None) -> None:
    token = create_access_token("user-123")
    assert isinstance(token, str)
    assert token


def test_decode_access_token_contains_subject(auth_settings: None) -> None:
    token = create_access_token("user-123")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"


def test_decode_access_token_contains_exp(auth_settings: None) -> None:
    token = create_access_token("user-123")
    payload = decode_access_token(token)
    assert isinstance(payload["exp"], int)


def test_decode_access_token_contains_iat(auth_settings: None) -> None:
    token = create_access_token("user-123")
    payload = decode_access_token(token)
    assert isinstance(payload["iat"], int)


def test_decode_access_token_contains_access_type(auth_settings: None) -> None:
    token = create_access_token("user-123")
    payload = decode_access_token(token)
    assert payload["type"] == "access"


def test_decode_access_token_rejects_expired_token(auth_settings: None) -> None:
    token = create_access_token(
        "user-123",
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(JWTError):
        decode_access_token(token)


def test_decode_access_token_rejects_invalid_token(auth_settings: None) -> None:
    with pytest.raises(JWTError):
        decode_access_token("not-a-valid-token")


def test_decode_access_token_uses_settings_secret_and_algorithm(
    auth_settings: None,
) -> None:
    token = create_access_token("user-123")
    settings = get_settings()
    assert settings.auth_secret_key == "test-secret-key-for-jwt"
    assert settings.auth_algorithm == "HS256"
    assert decode_access_token(token)["sub"] == "user-123"


def test_decode_access_token_rejects_wrong_token_type(auth_settings: None) -> None:
    from jose import jwt

    settings = Settings(
        auth_secret_key="test-secret-key-for-jwt",
        auth_algorithm="HS256",
    )
    token = jwt.encode(
        {"sub": "user-123", "type": "refresh"},
        settings.auth_secret_key,
        algorithm=settings.auth_algorithm,
    )
    with pytest.raises(JWTError, match="Invalid token type"):
        decode_access_token(token)
