"""Operations dashboard API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.workspace_deps import get_active_workspace_membership
from app.db.session import get_async_session
from app.models.workspace_membership import WorkspaceMembership
from app.schemas.operations_dashboard import OperationsDashboardRead
from app.services.operations_dashboard_service import get_operations_dashboard

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/operations",
    tags=["operations"],
)


def _envelope(data: dict) -> dict:
    return {"data": data, "meta": {}, "error": None}


@router.get("/dashboard")
async def get_workspace_operations_dashboard(
    workspace_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Return aggregated operational metrics for the workspace."""
    _ = membership
    dashboard = await get_operations_dashboard(session, workspace_id)
    return _envelope(
        OperationsDashboardRead.model_validate(dashboard).model_dump(mode="json")
    )
