"""Georgian CX Platform — FastAPI backend."""

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.case_tags import router as case_tags_router
from app.api.health import router as health_router
from app.api.operations_dashboard import router as operations_dashboard_router
from app.api.universal_cases import router as universal_cases_router
from app.api.workspaces import router as workspaces_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="Georgian CX Platform API",
        version="0.1.0",
        description=(
            "Georgian CX Platform backend. Health, auth, and workspace bootstrap API."
        ),
    )
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(workspaces_router)
    application.include_router(case_tags_router)
    application.include_router(universal_cases_router)
    application.include_router(operations_dashboard_router)
    return application


app = create_app()
