"""Authentication-related Pydantic schemas (no API routes yet)."""

from pydantic import BaseModel


class Token(BaseModel):
    """Access token response shape for future auth endpoints."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded access token claims."""

    sub: str
    exp: int | None = None
    type: str | None = None
