"""Tests for Agent Workforce API."""

import uuid
from datetime import UTC, datetime
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_case_metric import AgentCaseMetric
from app.models.agent_shift import AgentShift
from app.models.enums import (
    CaseStatus,
    WorkspaceMemberRole,
    WorkspaceMemberStatus,
)
from app.models.universal_case import UniversalCase
from app.models.workspace_membership import WorkspaceMembership
from tests.conftest import auth_headers, login_user, register_user, response_data

pytestmark = pytest.mark.asyncio


def _workforce_path(workspace_id: str, suffix: str) -> str:
    return f"/api/v1/workspaces/{workspace_id}/agent-workforce/{suffix}"


async def _auth(prefix: str, client: AsyncClient) -> dict[str, str]:
    return await auth_headers(client, f"{prefix}-{uuid.uuid4()}@example.com")


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
    title: str = "Workforce API case",
) -> str:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": title},
        headers=headers,
    )
    assert response.status_code == 201
    return response_data(response)["id"]


async def _clock_in(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: str,
):
    return await client.post(
        _workforce_path(workspace_id, "clock-in"),
        headers=headers,
    )


async def test_clock_in_unauthenticated_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        _workforce_path(str(uuid.uuid4()), "clock-in"),
    )
    assert response.status_code == 401


async def test_clock_in_non_member_returns_404(client: AsyncClient) -> None:
    owner_headers = await _auth("wf-owner", client)
    workspace_id = await _create_workspace(client, owner_headers, "WF Private")
    other_headers = await _auth("wf-other", client)

    response = await _clock_in(client, other_headers, workspace_id)
    assert response.status_code == 404


async def test_clock_in_creates_active_shift(client: AsyncClient) -> None:
    headers = await _auth("wf-clock-in", client)
    workspace_id = await _create_workspace(client, headers, "WF Clock In")
    me = response_data(await client.get("/api/v1/auth/me", headers=headers))

    response = await _clock_in(client, headers, workspace_id)
    assert response.status_code == 201
    data = response_data(response)
    assert data["workspace_id"] == workspace_id
    assert data["user_id"] == me["id"]
    assert data["is_active"] is True
    assert data["clock_in_at"]
    assert data["clock_out_at"] is None


async def test_duplicate_clock_in_returns_422(client: AsyncClient) -> None:
    headers = await _auth("wf-dup", client)
    workspace_id = await _create_workspace(client, headers, "WF Duplicate")

    first = await _clock_in(client, headers, workspace_id)
    assert first.status_code == 201

    second = await _clock_in(client, headers, workspace_id)
    assert second.status_code == 422
    assert second.json()["detail"] == (
        "Agent already has an active shift in this workspace"
    )


async def test_active_shift_endpoint_returns_current_user_shift(
    client: AsyncClient,
) -> None:
    headers = await _auth("wf-me-shift", client)
    workspace_id = await _create_workspace(client, headers, "WF Me Shift")

    empty = await client.get(
        _workforce_path(workspace_id, "me/active-shift"),
        headers=headers,
    )
    assert empty.status_code == 200
    assert response_data(empty) is None

    clock_in_response = await _clock_in(client, headers, workspace_id)
    assert clock_in_response.status_code == 201
    shift_id = response_data(clock_in_response)["id"]

    active = await client.get(
        _workforce_path(workspace_id, "me/active-shift"),
        headers=headers,
    )
    assert active.status_code == 200
    data = response_data(active)
    assert data is not None
    assert data["id"] == shift_id
    assert data["is_active"] is True


async def test_clock_out_closes_active_shift(client: AsyncClient) -> None:
    headers = await _auth("wf-clock-out", client)
    workspace_id = await _create_workspace(client, headers, "WF Clock Out")

    clock_in_response = await _clock_in(client, headers, workspace_id)
    assert clock_in_response.status_code == 201

    clock_out_response = await client.post(
        _workforce_path(workspace_id, "clock-out"),
        headers=headers,
    )
    assert clock_out_response.status_code == 200
    data = response_data(clock_out_response)
    assert data["is_active"] is False
    assert data["clock_out_at"] is not None

    active = await client.get(
        _workforce_path(workspace_id, "me/active-shift"),
        headers=headers,
    )
    assert response_data(active) is None


async def test_clock_out_without_active_shift_returns_422(
    client: AsyncClient,
) -> None:
    headers = await _auth("wf-no-shift", client)
    workspace_id = await _create_workspace(client, headers, "WF No Shift")

    response = await client.post(
        _workforce_path(workspace_id, "clock-out"),
        headers=headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == (
        "No active shift found for this agent in workspace"
    )


async def test_active_shifts_list_only_returns_workspace_shifts(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_headers = await _auth("wf-list-owner", client)
    workspace_a = await _create_workspace(client, owner_headers, "WF List A")
    workspace_b = await _create_workspace(client, owner_headers, "WF List B")

    member_email = f"wf-member-{uuid.uuid4()}@example.com"
    await register_user(client, email=member_email)
    member_headers = {
        "Authorization": f"Bearer {await login_user(client, email=member_email)}"
    }
    member_id = response_data(
        await client.get("/api/v1/auth/me", headers=member_headers)
    )["id"]

    db_session.add(
        WorkspaceMembership(
            workspace_id=UUID(workspace_a),
            user_id=UUID(member_id),
            role=WorkspaceMemberRole.MEMBER,
            status=WorkspaceMemberStatus.ACTIVE,
        )
    )
    await db_session.flush()

    owner_shift = await _clock_in(client, owner_headers, workspace_a)
    member_shift = await _clock_in(client, member_headers, workspace_a)
    assert owner_shift.status_code == 201
    assert member_shift.status_code == 201

    db_session.add(
        AgentShift(
            workspace_id=UUID(workspace_b),
            user_id=UUID(member_id),
            clock_in_at=datetime.now(UTC),
            is_active=True,
        )
    )
    await db_session.flush()

    response = await client.get(
        _workforce_path(workspace_a, "active-shifts"),
        headers=owner_headers,
    )
    assert response.status_code == 200
    items = response_data(response)
    assert len(items) == 2
    assert {item["workspace_id"] for item in items} == {workspace_a}
    assert {item["user_id"] for item in items} == {
        response_data(owner_shift)["user_id"],
        member_id,
    }


async def test_case_metrics_list_returns_workspace_metrics(
    client: AsyncClient,
) -> None:
    headers = await _auth("wf-metrics", client)
    workspace_id = await _create_workspace(client, headers, "WF Metrics")
    user_id = response_data(await client.get("/api/v1/auth/me", headers=headers))["id"]
    case_id = await _create_case(client, headers, workspace_id)

    await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}/comments",
        json={"body": "Agent reply"},
        headers=headers,
    )

    response = await client.get(
        _workforce_path(workspace_id, "case-metrics"),
        headers=headers,
    )
    assert response.status_code == 200
    items = response_data(response)
    assert len(items) == 1
    assert items[0]["workspace_id"] == workspace_id
    assert items[0]["case_id"] == case_id
    assert items[0]["user_id"] == user_id
    assert items[0]["messages_count"] == 1


async def test_case_metrics_filters_by_user_id(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_headers = await _auth("wf-filter-user", client)
    workspace_id = await _create_workspace(client, owner_headers, "WF Filter User")

    member_email = f"wf-filter-member-{uuid.uuid4()}@example.com"
    await register_user(client, email=member_email)
    member_headers = {
        "Authorization": f"Bearer {await login_user(client, email=member_email)}"
    }
    member_id = response_data(
        await client.get("/api/v1/auth/me", headers=member_headers)
    )["id"]

    db_session.add(
        WorkspaceMembership(
            workspace_id=UUID(workspace_id),
            user_id=UUID(member_id),
            role=WorkspaceMemberRole.MEMBER,
            status=WorkspaceMemberStatus.ACTIVE,
        )
    )
    await db_session.flush()

    owner_case = await _create_case(client, owner_headers, workspace_id, title="Owner")
    member_case = await _create_case(
        client,
        owner_headers,
        workspace_id,
        title="Member",
    )

    await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{member_case}",
        json={"assigned_to_user_id": member_id},
        headers=owner_headers,
    )
    await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases/{owner_case}/comments",
        json={"body": "Owner comment"},
        headers=owner_headers,
    )

    response = await client.get(
        _workforce_path(workspace_id, "case-metrics"),
        params={"user_id": member_id},
        headers=owner_headers,
    )
    assert response.status_code == 200
    items = response_data(response)
    assert len(items) == 1
    assert items[0]["user_id"] == member_id
    assert items[0]["case_id"] == member_case


async def test_case_metrics_filters_by_case_id(client: AsyncClient) -> None:
    headers = await _auth("wf-filter-case", client)
    workspace_id = await _create_workspace(client, headers, "WF Filter Case")
    case_a = await _create_case(client, headers, workspace_id, title="Case A")
    await _create_case(client, headers, workspace_id, title="Case B")

    await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_a}/comments",
        json={"body": "On case A"},
        headers=headers,
    )

    response = await client.get(
        _workforce_path(workspace_id, "case-metrics"),
        params={"case_id": case_a},
        headers=headers,
    )
    assert response.status_code == 200
    items = response_data(response)
    assert len(items) == 1
    assert items[0]["case_id"] == case_a


async def test_cross_workspace_data_is_excluded(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await _auth("wf-cross", client)
    workspace_a = await _create_workspace(client, headers, "WF Cross A")
    workspace_b = await _create_workspace(client, headers, "WF Cross B")
    user_id = response_data(await client.get("/api/v1/auth/me", headers=headers))["id"]

    other_case = UniversalCase(
        workspace_id=UUID(workspace_b),
        title="Foreign case",
        status=CaseStatus.OPEN,
    )
    db_session.add(other_case)
    await db_session.flush()
    db_session.add(
        AgentCaseMetric(
            workspace_id=UUID(workspace_b),
            case_id=other_case.id,
            user_id=UUID(user_id),
            messages_count=3,
        )
    )
    db_session.add(
        AgentShift(
            workspace_id=UUID(workspace_b),
            user_id=UUID(user_id),
            clock_in_at=datetime.now(UTC),
            is_active=True,
        )
    )
    await db_session.flush()

    shifts = await client.get(
        _workforce_path(workspace_a, "active-shifts"),
        headers=headers,
    )
    assert shifts.status_code == 200
    assert response_data(shifts) == []

    metrics = await client.get(
        _workforce_path(workspace_a, "case-metrics"),
        headers=headers,
    )
    assert metrics.status_code == 200
    assert response_data(metrics) == []
