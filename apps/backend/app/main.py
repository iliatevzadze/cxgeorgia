"""Georgian CX Platform — FastAPI backend."""

from fastapi import FastAPI

from app.api.health import router as health_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="Georgian CX Platform API",
        version="0.1.0",
        description=(
            "Phase 0 backend skeleton. Health check only — "
            "no database, auth, or business logic yet."
        ),
    )
    application.include_router(health_router)
    return application


app = create_app()
