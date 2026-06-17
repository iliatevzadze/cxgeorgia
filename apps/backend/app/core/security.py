"""Password hashing and JWT access token utilities."""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

BCRYPT_ROUNDS = 12
ACCESS_TOKEN_TYPE = "access"


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash for a plain-text password."""
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(plain_password.encode(), salt)
    return hashed.decode()


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Return True when the plain password matches the stored hash."""
    return bcrypt.checkpw(plain_password.encode(), password_hash.encode())


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token for the given subject."""
    settings = get_settings()
    now = datetime.now(UTC)
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.auth_access_token_expire_minutes)
    expire = now + expires_delta
    payload = {
        "sub": subject,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": ACCESS_TOKEN_TYPE,
    }
    return jwt.encode(
        payload,
        settings.auth_secret_key,
        algorithm=settings.auth_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.auth_secret_key,
            algorithms=[settings.auth_algorithm],
        )
    except JWTError as exc:
        raise JWTError("Invalid access token") from exc

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise JWTError("Invalid token type")

    return payload
