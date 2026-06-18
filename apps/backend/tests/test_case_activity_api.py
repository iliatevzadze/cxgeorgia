"""Tests for Universal Case activity API."""

import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_activity import CaseActivity
from app.models.enums import CaseActivityType, CaseStatus
from app.models.universal_case import UniversalCase
from tests.conftest import auth_headers, login_user, register_user, response_data

pytestmark = pytest.mark.asyncio


def _activities_path(workspace_id: str, case_id: str) -> str:
    return f"/api/v1/workspaces/{workspace_id}/cases/{case_id}/activities"


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
    title: str = "Activity test case",
) -> str:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": title},
        headers=headers,
    )
    assert response.status_code == 201
    return response_data(response)["id"]


async def _insert_activity(
    db_session: AsyncSession,
    *,
    workspace_id: str,
    case_id: str,
    activity_type: CaseActivityType = CaseActivityType.CASE_CREATED,
    actor_user_id: UUID | None = None,
    message: str | None = None,
    activity_metadata: dict | None = None,
    created_at: datetime | None = None,
) -> CaseActivity:
    activity = CaseActivity(
        workspace_id=UUID(workspace_id),
        case_id=UUID(case_id),
        actor_user_id=actor_user_id,
        activity_type=activity_type,
        message=message,
        activity_metadata=activity_metadata or {},
    )
    if created_at is not None:
        activity.created_at = created_at
    db_session.add(activity)
    await db_session.flush()
    return activity


async def test_list_activities_unauthenticated_returns_401(client: AsyncClient) -> None:
    response = await client.get(
        _activities_path(str(uuid.uuid4()), str(uuid.uuid4())),
    )
    assert response.status_code == 401


async def test_list_activities_as_workspace_member(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(client, f"activity-list-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Activity List Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    me_response = await client.get("/api/v1/auth/me", headers=headers)
    user_id = UUID(response_data(me_response)["id"])

    await _insert_activity(
        db_session,
        workspace_id=workspace_id,
        case_id=case_id,
        actor_user_id=user_id,
        activity_type=CaseActivityType.STATUS_CHANGED,
        message="Status changed",
        activity_metadata={"from": "open", "to": "pending"},
    )

    response = await client.get(
        _activities_path(workspace_id, case_id),
        headers=headers,
    )
    assert response.status_code == 200
    items = response_data(response)
    assert len(items) == 1
    assert items[0]["workspace_id"] == workspace_id
    assert items[0]["case_id"] == case_id
    assert items[0]["actor_user_id"] == str(user_id)
    assert items[0]["activity_type"] == CaseActivityType.STATUS_CHANGED.value
    assert items[0]["message"] == "Status changed"
    assert items[0]["metadata"] == {"from": "open", "to": "pending"}
    assert items[0]["id"]
    assert items[0]["created_at"]


async def test_list_activities_response_uses_envelope(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"activity-envelope-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Activity Envelope Workspace",
    )
    case_id = await _create_case(client, headers, workspace_id)

    await _insert_activity(
        db_session,
        workspace_id=workspace_id,
        case_id=case_id,
        message="Envelope activity",
    )

    response = await client.get(
        _activities_path(workspace_id, case_id),
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None
    assert payload["meta"] == {}
    assert isinstance(payload["data"], list)
    assert payload["data"][0]["message"] == "Envelope activity"


async def test_list_activities_metadata_serializes_as_metadata(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"activity-metadata-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Activity Metadata Workspace",
    )
    case_id = await _create_case(client, headers, workspace_id)

    await _insert_activity(
        db_session,
        workspace_id=workspace_id,
        case_id=case_id,
        activity_metadata={"field": "value"},
    )

    response = await client.get(
        _activities_path(workspace_id, case_id),
        headers=headers,
    )
    assert response.status_code == 200
    item = response_data(response)[0]
    assert "metadata" in item
    assert item["metadata"] == {"field": "value"}
    assert "activity_metadata" not in item


async def test_list_activities_actor_user_id_can_be_null(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"activity-null-actor-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Activity Null Actor Workspace",
    )
    case_id = await _create_case(client, headers, workspace_id)

    await _insert_activity(
        db_session,
        workspace_id=workspace_id,
        case_id=case_id,
        actor_user_id=None,
    )

    response = await client.get(
        _activities_path(workspace_id, case_id),
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)[0]["actor_user_id"] is None


async def test_list_activities_returns_newest_first(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(client, f"activity-order-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Activity Order Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    older = await _insert_activity(
        db_session,
        workspace_id=workspace_id,
        case_id=case_id,
        message="Older activity",
        created_at=datetime.now(UTC) - timedelta(hours=1),
    )
    newer = await _insert_activity(
        db_session,
        workspace_id=workspace_id,
        case_id=case_id,
        message="Newer activity",
        created_at=datetime.now(UTC),
    )

    response = await client.get(
        _activities_path(workspace_id, case_id),
        headers=headers,
    )
    assert response.status_code == 200
    items = response_data(response)
    assert [item["id"] for item in items] == [str(newer.id), str(older.id)]
    assert [item["message"] for item in items] == ["Newer activity", "Older activity"]


async def test_list_activities_excludes_other_case_in_same_workspace(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"activity-case-iso-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Activity Case Iso Workspace",
    )
    case_a = await _create_case(client, headers, workspace_id, title="Case A")
    case_b = await _create_case(client, headers, workspace_id, title="Case B")

    await _insert_activity(
        db_session,
        workspace_id=workspace_id,
        case_id=case_a,
        message="Activity on case A",
    )
    await _insert_activity(
        db_session,
        workspace_id=workspace_id,
        case_id=case_b,
        message="Activity on case B",
    )

    response = await client.get(
        _activities_path(workspace_id, case_a),
        headers=headers,
    )
    assert response.status_code == 200
    items = response_data(response)
    assert len(items) == 1
    assert items[0]["case_id"] == case_a
    assert items[0]["message"] == "Activity on case A"


async def test_list_activities_excludes_other_workspace(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"activity-workspace-iso-{uuid.uuid4()}@example.com",
    )
    workspace_a = await _create_workspace(client, headers, "Activity Workspace A")
    workspace_b = await _create_workspace(client, headers, "Activity Workspace B")
    case_a = await _create_case(client, headers, workspace_a, title="Case in A")

    await _insert_activity(
        db_session,
        workspace_id=workspace_a,
        case_id=case_a,
        message="Activity in workspace A",
    )

    other_case = UniversalCase(
        workspace_id=UUID(workspace_b),
        title="Case in B",
        status=CaseStatus.OPEN,
    )
    db_session.add(other_case)
    await db_session.flush()
    await _insert_activity(
        db_session,
        workspace_id=workspace_b,
        case_id=str(other_case.id),
        message="Activity in workspace B",
    )

    response = await client.get(
        _activities_path(workspace_a, case_a),
        headers=headers,
    )
    assert response.status_code == 200
    items = response_data(response)
    assert len(items) == 1
    assert items[0]["workspace_id"] == workspace_a
    assert items[0]["message"] == "Activity in workspace A"


async def test_list_activities_cross_workspace_returns_404(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"activity-cross-get-{uuid.uuid4()}@example.com",
    )
    workspace_a = await _create_workspace(client, headers, "Activity Cross Get A")
    workspace_b = await _create_workspace(client, headers, "Activity Cross Get B")
    case_id = await _create_case(client, headers, workspace_a)

    response = await client.get(
        _activities_path(workspace_b, case_id),
        headers=headers,
    )
    assert response.status_code == 404


async def test_list_activities_non_member_returns_404(client: AsyncClient) -> None:
    owner_email = f"activity-owner-list-{uuid.uuid4()}@example.com"
    other_email = f"activity-other-list-{uuid.uuid4()}@example.com"
    owner_headers = await auth_headers(client, owner_email)
    workspace_id = await _create_workspace(
        client,
        owner_headers,
        "Activity Private List",
    )
    case_id = await _create_case(client, owner_headers, workspace_id)

    await register_user(client, email=other_email)
    other_headers = {
        "Authorization": f"Bearer {await login_user(client, email=other_email)}"
    }
    response = await client.get(
        _activities_path(workspace_id, case_id),
        headers=other_headers,
    )
    assert response.status_code == 404


async def test_list_activities_nonexistent_case_returns_404(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"activity-missing-case-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Activity Missing Case Workspace",
    )

    response = await client.get(
        _activities_path(workspace_id, str(uuid.uuid4())),
        headers=headers,
    )
    assert response.status_code == 404


async def test_list_activities_empty_list_returns_empty_array(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"activity-empty-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Activity Empty Workspace",
    )
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.get(
        _activities_path(workspace_id, case_id),
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response) == []
