"""Georgian CX Platform — FastAPI backend."""

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.health import router as health_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="Georgian CX Platform API",
        version="0.1.0",
        description=(
            "Georgian CX Platform backend. Health check and Phase 1 auth API."
        ),
    )
    application.include_router(health_router)
    application.include_router(auth_router)
    return application


app = create_app()
