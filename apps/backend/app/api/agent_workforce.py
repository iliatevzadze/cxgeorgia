"""Agent workforce API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.workspace_deps import get_active_workspace_membership
from app.db.session import get_async_session
from app.models.user import User
from app.models.workspace_membership import WorkspaceMembership
from app.schemas.agent_workforce import (
    AgentCaseMetricRead,
    AgentShiftRead,
)
from app.services.agent_workforce_service import (
    DuplicateActiveShiftError,
    NoActiveShiftError,
    clock_in,
    clock_out,
    get_active_shift,
    list_active_workspace_shifts,
    list_workspace_case_metrics,
)

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/agent-workforce",
    tags=["agent-workforce"],
)


def _envelope(data: dict | list | None) -> dict:
    return {"data": data, "meta": {}, "error": None}


def _shift_payload(shift) -> dict:
    return AgentShiftRead.model_validate(shift).model_dump(mode="json")


@router.post("/clock-in", status_code=status.HTTP_201_CREATED)
async def agent_workforce_clock_in(
    workspace_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Start an active shift for the current user."""
    _ = membership

    try:
        shift = await clock_in(session, current_user.id, workspace_id)
        await session.commit()
    except DuplicateActiveShiftError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    await session.refresh(shift)
    return _envelope(_shift_payload(shift))


@router.post("/clock-out")
async def agent_workforce_clock_out(
    workspace_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Close the current user's active shift."""
    _ = membership

    try:
        shift = await clock_out(session, current_user.id, workspace_id)
        await session.commit()
    except NoActiveShiftError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    await session.refresh(shift)
    return _envelope(_shift_payload(shift))


@router.get("/me/active-shift")
async def get_my_active_shift(
    workspace_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Return the current user's active shift, if any."""
    _ = membership
    shift = await get_active_shift(session, current_user.id, workspace_id)
    if shift is None:
        return _envelope(None)
    return _envelope(_shift_payload(shift))


@router.get("/active-shifts")
async def list_active_shifts(
    workspace_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """List active shifts in the workspace."""
    _ = membership
    shifts = await list_active_workspace_shifts(session, workspace_id)
    items = [_shift_payload(shift) for shift in shifts]
    return _envelope(items)


@router.get("/case-metrics")
async def list_case_metrics(
    workspace_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
    user_id: UUID | None = Query(default=None),
    case_id: UUID | None = Query(default=None),
) -> dict:
    """List agent case metrics in the workspace."""
    _ = membership
    metrics = await list_workspace_case_metrics(
        session,
        workspace_id,
        user_id=user_id,
        case_id=case_id,
    )
    items = [
        AgentCaseMetricRead.model_validate(metric).model_dump(mode="json")
        for metric in metrics
    ]
    return _envelope(items)
