"""Tests for auth Pydantic schemas."""

from app.schemas.auth import Token, TokenPayload


def test_token_schema_defaults_token_type_to_bearer() -> None:
    token = Token(access_token="signed.jwt.token")
    assert token.token_type == "bearer"


def test_token_payload_accepts_subject_and_metadata() -> None:
    payload = TokenPayload(sub="user-123", exp=1_700_000_000, type="access")
    assert payload.sub == "user-123"
    assert payload.exp == 1_700_000_000
    assert payload.type == "access"
