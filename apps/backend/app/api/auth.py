"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ACCOUNT_DISABLED_MESSAGE, get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_async_session
from app.models.enums import UserStatus
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserLogin, UserRead

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

INVALID_CREDENTIALS_MESSAGE = "Invalid email or password"


def _envelope(data: dict | list) -> dict:
    return {"data": data, "meta": {}, "error": None}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: UserCreate,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Register a new user account."""
    existing_user = await session.scalar(
        select(User).where(User.email == body.email),
    )
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        status=UserStatus.ACTIVE,
        is_email_verified=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return _envelope(UserRead.model_validate(user).model_dump(mode="json"))


@router.post("/login")
async def login(
    body: UserLogin,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Authenticate with email and password; returns a bearer access token."""
    user = await session.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_MESSAGE,
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ACCOUNT_DISABLED_MESSAGE,
        )

    access_token = create_access_token(str(user.id))
    token = Token(access_token=access_token)
    return _envelope(token.model_dump())


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)) -> dict:
    """Return the currently authenticated user."""
    return _envelope(UserRead.model_validate(current_user).model_dump(mode="json"))
