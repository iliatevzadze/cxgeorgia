"""Tests for agent workforce shift and case metrics."""

import uuid
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_case_metric import AgentCaseMetric
from app.models.enums import (
    CaseStatus,
    UserStatus,
    WorkspaceMemberRole,
    WorkspaceMemberStatus,
    WorkspaceStatus,
)
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_membership import WorkspaceMembership
from app.services.agent_workforce_service import (
    DuplicateActiveShiftError,
    NoActiveShiftError,
    clock_in,
    clock_out,
    get_active_shift,
)
from tests.conftest import auth_headers, register_user, response_data

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
    title: str = "Workforce test case",
) -> str:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": title},
        headers=headers,
    )
    assert response.status_code == 201
    return response_data(response)["id"]


async def _get_user_id(client: AsyncClient, headers: dict[str, str]) -> str:
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    return response_data(response)["id"]


async def _add_active_workspace_member(
    db_session: AsyncSession,
    workspace_id: str,
    *,
    email: str,
    client: AsyncClient,
) -> str:
    await register_user(client, email=email)
    user = await db_session.scalar(select(User).where(User.email == email))
    assert user is not None
    db_session.add(
        WorkspaceMembership(
            workspace_id=UUID(workspace_id),
            user_id=user.id,
            role=WorkspaceMemberRole.MEMBER,
            status=WorkspaceMemberStatus.ACTIVE,
        )
    )
    await db_session.flush()
    return str(user.id)


async def _create_workspace_user(
    db_session: AsyncSession,
) -> tuple[Workspace, User]:
    suffix = uuid.uuid4().hex[:12]
    user = User(
        email=f"workforce-unit-{suffix}@example.com",
        password_hash="hashed-password",
        full_name="Workforce Unit User",
        status=UserStatus.ACTIVE,
    )
    workspace = Workspace(
        name=f"Workforce Workspace {suffix}",
        slug=f"workforce-workspace-{suffix}",
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
    return workspace, user


async def _load_case_metric(
    db_session: AsyncSession,
    *,
    case_id: str,
    user_id: str,
) -> AgentCaseMetric:
    metric = await db_session.scalar(
        select(AgentCaseMetric).where(
            AgentCaseMetric.case_id == UUID(case_id),
            AgentCaseMetric.user_id == UUID(user_id),
        )
    )
    assert metric is not None
    return metric


async def test_clock_in_creates_active_shift(db_session: AsyncSession) -> None:
    workspace, user = await _create_workspace_user(db_session)

    shift = await clock_in(db_session, user.id, workspace.id)

    assert shift.is_active is True
    assert shift.clock_in_at is not None
    assert shift.clock_out_at is None
    active = await get_active_shift(db_session, user.id, workspace.id)
    assert active is not None
    assert active.id == shift.id


async def test_duplicate_active_shift_prevented(db_session: AsyncSession) -> None:
    workspace, user = await _create_workspace_user(db_session)
    await clock_in(db_session, user.id, workspace.id)

    with pytest.raises(DuplicateActiveShiftError):
        await clock_in(db_session, user.id, workspace.id)


async def test_clock_out_closes_shift(db_session: AsyncSession) -> None:
    workspace, user = await _create_workspace_user(db_session)
    await clock_in(db_session, user.id, workspace.id)

    closed = await clock_out(db_session, user.id, workspace.id)

    assert closed.is_active is False
    assert closed.clock_out_at is not None
    assert await get_active_shift(db_session, user.id, workspace.id) is None


async def test_clock_out_without_active_shift_raises(db_session: AsyncSession) -> None:
    workspace, user = await _create_workspace_user(db_session)

    with pytest.raises(NoActiveShiftError):
        await clock_out(db_session, user.id, workspace.id)


async def test_metrics_created_on_assignment(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_headers = await auth_headers(
        client,
        f"workforce-assign-owner-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        owner_headers,
        "Workforce Assign Workspace",
    )
    assignee_id = await _add_active_workspace_member(
        db_session,
        workspace_id,
        email=f"workforce-assignee-{uuid.uuid4()}@example.com",
        client=client,
    )
    case_id = await _create_case(client, owner_headers, workspace_id)

    response = await client.patch(
        _case_path(workspace_id, case_id),
        json={"assigned_to_user_id": assignee_id},
        headers=owner_headers,
    )
    assert response.status_code == 200

    metric = await _load_case_metric(
        db_session,
        case_id=case_id,
        user_id=assignee_id,
    )
    assert metric.assigned_at is not None
    assert metric.first_response_at is None
    assert metric.resolved_at is None


async def test_first_response_recorded_on_comment(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"workforce-comment-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Workforce Comment Workspace",
    )
    user_id = await _get_user_id(client, headers)
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.post(
        _comments_path(workspace_id, case_id),
        json={"body": "Hello customer"},
        headers=headers,
    )
    assert response.status_code == 201

    metric = await _load_case_metric(
        db_session,
        case_id=case_id,
        user_id=user_id,
    )
    assert metric.first_response_at is not None
    assert metric.messages_count == 1


async def test_resolution_recorded_on_status_update(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"workforce-resolve-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Workforce Resolve Workspace",
    )
    user_id = await _get_user_id(client, headers)
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        _case_path(workspace_id, case_id),
        json={"status": CaseStatus.RESOLVED.value},
        headers=headers,
    )
    assert response.status_code == 200

    metric = await _load_case_metric(
        db_session,
        case_id=case_id,
        user_id=user_id,
    )
    assert metric.first_response_at is not None
    assert metric.resolved_at is not None


async def test_assignment_on_case_create_records_metric(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_headers = await auth_headers(
        client,
        f"workforce-create-assign-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        owner_headers,
        "Workforce Create Assign Workspace",
    )
    assignee_id = await _add_active_workspace_member(
        db_session,
        workspace_id,
        email=f"workforce-create-assignee-{uuid.uuid4()}@example.com",
        client=client,
    )

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Assigned at create", "assigned_to_user_id": assignee_id},
        headers=owner_headers,
    )
    assert response.status_code == 201
    case_id = response_data(response)["id"]

    metric = await _load_case_metric(
        db_session,
        case_id=case_id,
        user_id=assignee_id,
    )
    assert metric.assigned_at is not None
