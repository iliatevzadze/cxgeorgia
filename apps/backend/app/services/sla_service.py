"""Universal Case SLA tracking helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.models.enums import SlaStatus
from app.models.universal_case import UniversalCase

AT_RISK_FRACTION = 0.25


def _utc_now() -> datetime:
    return datetime.now(UTC)


def calculate_sla(case: UniversalCase, *, now: datetime | None = None) -> SlaStatus:
    """Determine SLA status from due dates and completion timestamps."""
    current = now or _utc_now()

    if _is_first_response_breached(case, current):
        return SlaStatus.BREACHED
    if _is_resolution_breached(case, current):
        return SlaStatus.BREACHED
    if _is_first_response_at_risk(case, current):
        return SlaStatus.AT_RISK
    if _is_resolution_at_risk(case, current):
        return SlaStatus.AT_RISK
    return SlaStatus.ON_TRACK


def update_sla_on_case_create(case: UniversalCase) -> None:
    """Set default SLA deadlines when a case is created."""
    settings = get_settings()
    anchor = case.created_at or _utc_now()
    case.first_response_due_at = anchor + timedelta(
        minutes=settings.default_first_response_minutes,
    )
    case.resolution_due_at = anchor + timedelta(
        minutes=settings.default_resolution_minutes,
    )
    case.sla_status = calculate_sla(case)


def mark_first_response(case: UniversalCase, *, now: datetime | None = None) -> None:
    """Record first agent response and refresh SLA status."""
    current = now or _utc_now()
    if case.first_response_at is None:
        case.first_response_at = current
    case.sla_status = calculate_sla(case, now=current)


def mark_resolved(case: UniversalCase, *, now: datetime | None = None) -> None:
    """Record case resolution and refresh SLA status."""
    current = now or _utc_now()
    if case.resolved_at is None:
        case.resolved_at = current
    case.sla_status = calculate_sla(case, now=current)


def _is_first_response_breached(case: UniversalCase, now: datetime) -> bool:
    if case.first_response_at is not None:
        return False
    if case.first_response_due_at is None:
        return False
    return now > case.first_response_due_at


def _is_resolution_breached(case: UniversalCase, now: datetime) -> bool:
    if case.resolved_at is not None:
        return False
    if case.resolution_due_at is None:
        return False
    return now > case.resolution_due_at


def _is_first_response_at_risk(case: UniversalCase, now: datetime) -> bool:
    if case.first_response_at is not None:
        return False
    if case.first_response_due_at is None or case.created_at is None:
        return False
    if now >= case.first_response_due_at:
        return False
    window = case.first_response_due_at - case.created_at
    remaining = case.first_response_due_at - now
    return remaining <= window * AT_RISK_FRACTION


def _is_resolution_at_risk(case: UniversalCase, now: datetime) -> bool:
    if case.resolved_at is not None:
        return False
    if case.resolution_due_at is None or case.created_at is None:
        return False
    if now >= case.resolution_due_at:
        return False
    window = case.resolution_due_at - case.created_at
    remaining = case.resolution_due_at - now
    return remaining <= window * AT_RISK_FRACTION
