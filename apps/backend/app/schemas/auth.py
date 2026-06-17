"""Authentication-related Pydantic schemas."""

from pydantic import BaseModel

from app.schemas.user import UserCreate, UserLogin, UserRead

__all__ = [
    "Token",
    "TokenPayload",
    "UserCreate",
    "UserLogin",
    "UserRead",
]


class Token(BaseModel):
    """Access token response."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded access token claims."""

    sub: str
    exp: int | None = None
    type: str | None = None
