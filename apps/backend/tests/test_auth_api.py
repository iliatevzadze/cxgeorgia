"""Tests for auth API endpoints."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.enums import UserStatus
from app.models.user import User
from tests.conftest import response_data

pytestmark = pytest.mark.asyncio


async def test_register_creates_user(client: AsyncClient) -> None:
    email = f"register-{uuid.uuid4()}@example.com"
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPass123",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201
    data = response_data(response)
    assert data["email"] == email.lower()
    assert data["full_name"] == "Test User"
    assert data["status"] == "active"
    assert data["is_email_verified"] is False
    assert "password_hash" not in data


async def test_register_normalizes_email_to_lowercase(client: AsyncClient) -> None:
    suffix = uuid.uuid4()
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"MixedCase.{suffix}@Example.COM",
            "password": "StrongPass123",
        },
    )
    assert response.status_code == 201
    assert response_data(response)["email"] == f"mixedcase.{suffix}@example.com"


async def test_register_stores_password_hash_not_plain_password(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    email = f"hash-check-{uuid.uuid4()}@example.com"
    password = "StrongPass123"
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201

    user = await db_session.scalar(select(User).where(User.email == email))
    assert user is not None
    assert user.password_hash != password
    assert user.password_hash.startswith("$2b$")


async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    email = f"duplicate-{uuid.uuid4()}@example.com"
    payload = {"email": email, "password": "StrongPass123"}
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


async def test_register_short_password_returns_validation_error(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"short-{uuid.uuid4()}@example.com",
            "password": "short",
        },
    )
    assert response.status_code == 422


async def test_login_returns_bearer_token(client: AsyncClient) -> None:
    email = f"login-{uuid.uuid4()}@example.com"
    password = "StrongPass123"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    data = response_data(response)
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert data["access_token"]


async def test_login_wrong_password_returns_401(client: AsyncClient) -> None:
    email = f"wrong-pass-{uuid.uuid4()}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPass123"},
    )
    assert response.status_code == 401


async def test_login_unknown_user_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": f"missing-{uuid.uuid4()}@example.com",
            "password": "StrongPass123",
        },
    )
    assert response.status_code == 401


async def test_login_disabled_user_returns_403(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    email = f"disabled-{uuid.uuid4()}@example.com"
    password = "StrongPass123"
    user = User(
        email=email,
        password_hash=hash_password(password),
        status=UserStatus.DISABLED,
        is_email_verified=False,
    )
    db_session.add(user)
    await db_session.flush()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 403


async def test_me_returns_current_user(client: AsyncClient) -> None:
    email = f"me-{uuid.uuid4()}@example.com"
    password = "StrongPass123"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Me User"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = response_data(login_response)["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response_data(response)
    assert data["email"] == email
    assert data["full_name"] == "Me User"
    assert "password_hash" not in data


async def test_me_missing_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_me_invalid_token_returns_401(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert response.status_code == 401


async def test_me_disabled_user_returns_403(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    email = f"me-disabled-{uuid.uuid4()}@example.com"
    password = "StrongPass123"
    user = User(
        email=email,
        password_hash=hash_password(password),
        status=UserStatus.DISABLED,
        is_email_verified=False,
    )
    db_session.add(user)
    await db_session.flush()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 403

    from app.core.security import create_access_token

    token = create_access_token(str(user.id))
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
