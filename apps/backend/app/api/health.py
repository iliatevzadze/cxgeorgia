"""Health check endpoint."""

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "data": {
            "status": "ok",
            "service": "backend",
            "app_name": settings.app_name,
            "environment": settings.app_env,
        },
        "meta": {},
        "error": None,
    }
