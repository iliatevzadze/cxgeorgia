"""Agent workforce shift and case metrics helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_case_metric import AgentCaseMetric
from app.models.agent_shift import AgentShift
from app.models.universal_case import UniversalCase


class DuplicateActiveShiftError(Exception):
    """Raised when an agent already has an active shift in a workspace."""


class NoActiveShiftError(Exception):
    """Raised when clock-out is requested without an active shift."""


def _utc_now() -> datetime:
    return datetime.now(UTC)


async def get_active_shift(
    session: AsyncSession,
    user_id: UUID,
    workspace_id: UUID,
) -> AgentShift | None:
    """Return the agent's active shift in the workspace, if any."""
    return await session.scalar(
        select(AgentShift).where(
            AgentShift.workspace_id == workspace_id,
            AgentShift.user_id == user_id,
            AgentShift.is_active.is_(True),
        )
    )


async def clock_in(
    session: AsyncSession,
    user_id: UUID,
    workspace_id: UUID,
    *,
    clock_in_at: datetime | None = None,
) -> AgentShift:
    """Start an active shift for the agent in the workspace."""
    active = await get_active_shift(session, user_id, workspace_id)
    if active is not None:
        raise DuplicateActiveShiftError(
            "Agent already has an active shift in this workspace",
        )

    shift = AgentShift(
        workspace_id=workspace_id,
        user_id=user_id,
        clock_in_at=clock_in_at or _utc_now(),
        is_active=True,
    )
    session.add(shift)
    await session.flush()
    return shift


async def clock_out(
    session: AsyncSession,
    user_id: UUID,
    workspace_id: UUID,
    *,
    clock_out_at: datetime | None = None,
) -> AgentShift:
    """Close the agent's active shift in the workspace."""
    shift = await get_active_shift(session, user_id, workspace_id)
    if shift is None:
        raise NoActiveShiftError("No active shift found for this agent in workspace")

    current = clock_out_at or _utc_now()
    shift.clock_out_at = current
    shift.is_active = False
    await session.flush()
    return shift


async def _get_or_create_case_metric(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    case_id: UUID,
    user_id: UUID,
) -> AgentCaseMetric:
    metric = await session.scalar(
        select(AgentCaseMetric).where(
            AgentCaseMetric.workspace_id == workspace_id,
            AgentCaseMetric.case_id == case_id,
            AgentCaseMetric.user_id == user_id,
        )
    )
    if metric is not None:
        return metric

    metric = AgentCaseMetric(
        workspace_id=workspace_id,
        case_id=case_id,
        user_id=user_id,
    )
    session.add(metric)
    await session.flush()
    return metric


async def record_case_assignment(
    session: AsyncSession,
    case: UniversalCase,
    user_id: UUID,
    *,
    assigned_at: datetime | None = None,
) -> AgentCaseMetric:
    """Create or update per-case metrics when an agent is assigned."""
    metric = await _get_or_create_case_metric(
        session,
        workspace_id=case.workspace_id,
        case_id=case.id,
        user_id=user_id,
    )
    if metric.assigned_at is None:
        metric.assigned_at = assigned_at or _utc_now()
    await session.flush()
    return metric


async def record_case_first_response(
    session: AsyncSession,
    case: UniversalCase,
    user_id: UUID,
    *,
    first_response_at: datetime | None = None,
) -> AgentCaseMetric:
    """Record first agent response on a case."""
    metric = await _get_or_create_case_metric(
        session,
        workspace_id=case.workspace_id,
        case_id=case.id,
        user_id=user_id,
    )
    if metric.first_response_at is None:
        metric.first_response_at = first_response_at or _utc_now()
    await session.flush()
    return metric


async def record_case_resolution(
    session: AsyncSession,
    case: UniversalCase,
    user_id: UUID,
    *,
    resolved_at: datetime | None = None,
) -> AgentCaseMetric:
    """Record case resolution by an agent."""
    metric = await _get_or_create_case_metric(
        session,
        workspace_id=case.workspace_id,
        case_id=case.id,
        user_id=user_id,
    )
    if metric.resolved_at is None:
        metric.resolved_at = resolved_at or _utc_now()
    await session.flush()
    return metric


async def record_agent_message(
    session: AsyncSession,
    case: UniversalCase,
    user_id: UUID,
) -> AgentCaseMetric:
    """Increment message count for an agent on a case."""
    metric = await _get_or_create_case_metric(
        session,
        workspace_id=case.workspace_id,
        case_id=case.id,
        user_id=user_id,
    )
    metric.messages_count += 1
    await session.flush()
    return metric


async def list_active_workspace_shifts(
    session: AsyncSession,
    workspace_id: UUID,
) -> list[AgentShift]:
    """Return active shifts in a workspace, newest clock-in first."""
    result = await session.scalars(
        select(AgentShift)
        .where(
            AgentShift.workspace_id == workspace_id,
            AgentShift.is_active.is_(True),
        )
        .order_by(AgentShift.clock_in_at.desc())
    )
    return list(result.all())


async def list_workspace_case_metrics(
    session: AsyncSession,
    workspace_id: UUID,
    *,
    user_id: UUID | None = None,
    case_id: UUID | None = None,
) -> list[AgentCaseMetric]:
    """Return workspace agent case metrics with optional filters."""
    query = select(AgentCaseMetric).where(
        AgentCaseMetric.workspace_id == workspace_id,
    )
    if user_id is not None:
        query = query.where(AgentCaseMetric.user_id == user_id)
    if case_id is not None:
        query = query.where(AgentCaseMetric.case_id == case_id)
    query = query.order_by(AgentCaseMetric.assigned_at.desc().nullslast())
    result = await session.scalars(query)
    return list(result.all())
