"""Tests for Universal Case SLA tracking."""

import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.enums import (
    CaseStatus,
    SlaStatus,
    UserStatus,
    WorkspaceMemberRole,
    WorkspaceMemberStatus,
    WorkspaceStatus,
)
from app.models.universal_case import UniversalCase
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_membership import WorkspaceMembership
from app.services.sla_service import (
    AT_RISK_FRACTION,
    calculate_sla,
    mark_first_response,
    update_sla_on_case_create,
)
from tests.conftest import auth_headers, response_data

pytestmark = pytest.mark.asyncio


def _case_path(workspace_id: str, case_id: str) -> str:
    return f"/api/v1/workspaces/{workspace_id}/cases/{case_id}"


def _comments_path(workspace_id: str, case_id: str) -> str:
    return f"{_case_path(workspace_id, case_id)}/comments"


async def _create_workspace(
    client: AsyncClient,
    headers: dict[str, str],
    name: str,
) -> str:
    response = await client.post(
        "/api/v1/workspaces",
        json={"name": name},
        headers=headers,
    )
    assert response.status_code == 201
    return response_data(response)["workspace"]["id"]


async def _create_case(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: str,
    *,
    title: str = "SLA test case",
) -> str:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": title},
        headers=headers,
    )
    assert response.status_code == 201
    return response_data(response)["id"]


async def _load_case(
    db_session: AsyncSession,
    case_id: str,
) -> UniversalCase:
    case = await db_session.scalar(
        select(UniversalCase).where(UniversalCase.id == UUID(case_id))
    )
    assert case is not None
    return case


async def _create_db_case(
    db_session: AsyncSession,
    *,
    created_at: datetime | None = None,
) -> UniversalCase:
    suffix = uuid.uuid4().hex[:12]
    user = User(
        email=f"sla-unit-{suffix}@example.com",
        password_hash="hashed-password",
        full_name="SLA Unit User",
        status=UserStatus.ACTIVE,
    )
    workspace = Workspace(
        name=f"SLA Workspace {suffix}",
        slug=f"sla-workspace-{suffix}",
        status=WorkspaceStatus.ACTIVE,
    )
    db_session.add_all([user, workspace])
    await db_session.flush()

    db_session.add(
        WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=user.id,
            role=WorkspaceMemberRole.OWNER,
            status=WorkspaceMemberStatus.ACTIVE,
        )
    )
    await db_session.flush()

    anchor = created_at or datetime.now(UTC)
    case = UniversalCase(
        workspace_id=workspace.id,
        title="Unit SLA case",
        status=CaseStatus.OPEN,
        created_by_user_id=user.id,
        created_at=anchor,
        updated_at=anchor,
    )
    db_session.add(case)
    await db_session.flush()
    return case


async def test_sla_defaults_set_on_case_create(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    settings = get_settings()
    headers = await auth_headers(client, f"sla-create-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "SLA Create Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    case = await _load_case(db_session, case_id)
    assert case.first_response_due_at == case.created_at + timedelta(
        minutes=settings.default_first_response_minutes,
    )
    assert case.resolution_due_at == case.created_at + timedelta(
        minutes=settings.default_resolution_minutes,
    )
    assert case.first_response_at is None
    assert case.resolved_at is None
    assert case.sla_status == SlaStatus.ON_TRACK


async def test_first_comment_marks_first_response(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(client, f"sla-comment-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "SLA Comment Workspace")
    case_id = await _create_case(client, headers, workspace_id)
    before = await _load_case(db_session, case_id)
    assert before.first_response_at is None

    response = await client.post(
        _comments_path(workspace_id, case_id),
        json={"body": "Agent reply"},
        headers=headers,
    )
    assert response.status_code == 201

    case = await _load_case(db_session, case_id)
    assert case.first_response_at is not None
    assert case.sla_status == SlaStatus.ON_TRACK


async def test_case_patch_marks_first_response(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(client, f"sla-patch-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "SLA Patch Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        _case_path(workspace_id, case_id),
        json={"priority": "high"},
        headers=headers,
    )
    assert response.status_code == 200

    case = await _load_case(db_session, case_id)
    assert case.first_response_at is not None
    assert case.sla_status == SlaStatus.ON_TRACK


async def test_resolution_marks_resolved_at_and_sla(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(client, f"sla-resolve-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "SLA Resolve Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        _case_path(workspace_id, case_id),
        json={"status": CaseStatus.RESOLVED.value},
        headers=headers,
    )
    assert response.status_code == 200

    case = await _load_case(db_session, case_id)
    assert case.first_response_at is not None
    assert case.resolved_at is not None
    assert case.sla_status == SlaStatus.ON_TRACK


async def test_overdue_first_response_becomes_breached(
    db_session: AsyncSession,
) -> None:
    anchor = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    case = await _create_db_case(db_session, created_at=anchor)
    update_sla_on_case_create(case)

    overdue = case.first_response_due_at + timedelta(minutes=1)
    assert calculate_sla(case, now=overdue) == SlaStatus.BREACHED


async def test_overdue_resolution_becomes_breached(
    db_session: AsyncSession,
) -> None:
    anchor = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    case = await _create_db_case(db_session, created_at=anchor)
    update_sla_on_case_create(case)
    mark_first_response(case, now=anchor + timedelta(minutes=5))

    overdue = case.resolution_due_at + timedelta(minutes=1)
    assert calculate_sla(case, now=overdue) == SlaStatus.BREACHED


async def test_sla_status_transitions_to_at_risk(
    db_session: AsyncSession,
) -> None:
    anchor = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    case = await _create_db_case(db_session, created_at=anchor)
    update_sla_on_case_create(case)

    response_window = case.first_response_due_at - case.created_at
    at_risk_moment = case.first_response_due_at - (
        response_window * AT_RISK_FRACTION / 2
    )
    assert calculate_sla(case, now=at_risk_moment) == SlaStatus.AT_RISK

    mark_first_response(case, now=at_risk_moment)
    assert case.sla_status == SlaStatus.ON_TRACK


async def test_late_first_response_clears_breach_after_recorded(
    db_session: AsyncSession,
) -> None:
    anchor = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    case = await _create_db_case(db_session, created_at=anchor)
    update_sla_on_case_create(case)

    overdue_response = case.first_response_due_at + timedelta(minutes=30)
    assert calculate_sla(case, now=overdue_response) == SlaStatus.BREACHED

    mark_first_response(case, now=overdue_response)
    assert case.first_response_at == overdue_response
    assert case.sla_status == SlaStatus.ON_TRACK


async def test_update_sla_on_case_create_sets_on_track(
    db_session: AsyncSession,
) -> None:
    case = await _create_db_case(db_session)
    update_sla_on_case_create(case)

    assert case.first_response_due_at is not None
    assert case.resolution_due_at is not None
    assert case.sla_status == SlaStatus.ON_TRACK
