"""Tests for auth dependencies."""

import uuid

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password
from app.models.enums import UserStatus
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def test_get_current_user_returns_active_user(db_session: AsyncSession) -> None:
    user = User(
        email=f"dep-{uuid.uuid4()}@example.com",
        password_hash=hash_password("StrongPass123"),
        status=UserStatus.ACTIVE,
        is_email_verified=False,
    )
    db_session.add(user)
    await db_session.flush()

    token = create_access_token(str(user.id))
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )
    current_user = await get_current_user(credentials, db_session)
    assert current_user.id == user.id


async def test_get_current_user_rejects_missing_credentials(
    db_session: AsyncSession,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(None, db_session)
    assert exc_info.value.status_code == 401
