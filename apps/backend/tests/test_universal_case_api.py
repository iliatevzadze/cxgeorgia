"""Tests for Universal Case API."""

import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import CasePriority, CaseSource, CaseStatus
from app.models.universal_case import UniversalCase
from tests.conftest import auth_headers, login_user, register_user, response_data

pytestmark = pytest.mark.asyncio


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


async def test_create_case_unauthenticated_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        f"/api/v1/workspaces/{uuid.uuid4()}/cases",
        json={"title": "Test Case"},
    )
    assert response.status_code == 401


async def test_list_cases_unauthenticated_returns_401(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/workspaces/{uuid.uuid4()}/cases")
    assert response.status_code == 401


async def test_get_case_unauthenticated_returns_401(client: AsyncClient) -> None:
    response = await client.get(
        f"/api/v1/workspaces/{uuid.uuid4()}/cases/{uuid.uuid4()}",
    )
    assert response.status_code == 401


async def test_create_case_as_workspace_member(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"case-create-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Case Workspace")
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Customer inquiry"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response_data(response)
    assert data["title"] == "Customer inquiry"
    assert data["workspace_id"] == workspace_id


async def test_create_case_sets_workspace_id_from_path(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"case-wsid-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Scoped Workspace")
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Scoped case"},
        headers=headers,
    )
    assert response_data(response)["workspace_id"] == workspace_id


async def test_create_case_sets_created_by_user_id(client: AsyncClient) -> None:
    email = f"case-creator-{uuid.uuid4()}@example.com"
    headers = await auth_headers(client, email)
    workspace_id = await _create_workspace(client, headers, "Creator Workspace")
    me_response = await client.get("/api/v1/auth/me", headers=headers)
    user_id = response_data(me_response)["id"]
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Authored case"},
        headers=headers,
    )
    assert response_data(response)["created_by_user_id"] == user_id


async def test_create_case_applies_default_status_priority_source(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"case-defaults-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Defaults Workspace")
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Default fields"},
        headers=headers,
    )
    data = response_data(response)
    assert data["status"] == CaseStatus.OPEN.value
    assert data["priority"] == CasePriority.NORMAL.value
    assert data["source"] == CaseSource.MANUAL.value


async def test_create_case_accepts_explicit_status_priority_source(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"case-explicit-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Explicit Workspace")
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={
            "title": "Explicit fields",
            "status": "pending",
            "priority": "high",
            "source": "email",
        },
        headers=headers,
    )
    data = response_data(response)
    assert data["status"] == CaseStatus.PENDING.value
    assert data["priority"] == CasePriority.HIGH.value
    assert data["source"] == CaseSource.EMAIL.value


async def test_create_case_empty_title_returns_422(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"case-empty-title-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Validation Workspace")
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": ""},
        headers=headers,
    )
    assert response.status_code == 422


async def test_create_case_whitespace_title_returns_422(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-whitespace-title-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Whitespace Workspace")
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "   "},
        headers=headers,
    )
    assert response.status_code == 422


async def test_create_case_trims_title(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"case-trim-title-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Trim Workspace")
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "  Valid title  "},
        headers=headers,
    )
    assert response.status_code == 201
    assert response_data(response)["title"] == "Valid title"


async def test_create_case_missing_title_returns_422(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"case-no-title-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "No Title Workspace")
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={},
        headers=headers,
    )
    assert response.status_code == 422


async def test_list_cases_for_workspace_member(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"case-list-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "List Workspace")
    create_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Listed case"},
        headers=headers,
    )
    case_id = response_data(create_response)["id"]

    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        headers=headers,
    )
    assert list_response.status_code == 200
    items = response_data(list_response)
    assert len(items) == 1
    assert items[0]["id"] == case_id


async def test_list_cases_excludes_other_workspace_cases(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(client, f"case-list-iso-{uuid.uuid4()}@example.com")
    workspace_a = await _create_workspace(client, headers, "Workspace A")
    workspace_b = await _create_workspace(client, headers, "Workspace B")

    await client.post(
        f"/api/v1/workspaces/{workspace_a}/cases",
        json={"title": "Case in A"},
        headers=headers,
    )
    other_case = UniversalCase(
        workspace_id=UUID(workspace_b),
        title="Case in B",
        status=CaseStatus.OPEN,
        priority=CasePriority.NORMAL,
        source=CaseSource.MANUAL,
    )
    db_session.add(other_case)
    await db_session.flush()

    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_a}/cases",
        headers=headers,
    )
    items = response_data(list_response)
    assert len(items) == 1
    assert items[0]["title"] == "Case in A"
    assert items[0]["workspace_id"] == workspace_a


async def test_list_cases_sorted_newest_first(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(client, f"case-list-order-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Order Workspace")
    first = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "First case"},
        headers=headers,
    )
    second = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Second case"},
        headers=headers,
    )
    first_id = response_data(first)["id"]
    second_id = response_data(second)["id"]
    first_case = await db_session.get(UniversalCase, UUID(first_id))
    assert first_case is not None
    first_case.created_at = datetime.now(UTC) - timedelta(hours=1)
    await db_session.flush()

    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        headers=headers,
    )
    items = response_data(list_response)
    assert [item["id"] for item in items] == [second_id, first_id]


async def test_get_case_detail_for_workspace_member(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"case-detail-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Detail Workspace")
    create_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Detail case"},
        headers=headers,
    )
    case_id = response_data(create_response)["id"]

    detail_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        headers=headers,
    )
    assert detail_response.status_code == 200
    assert response_data(detail_response)["title"] == "Detail case"


async def test_get_case_from_other_workspace_path_returns_404(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"case-cross-{uuid.uuid4()}@example.com")
    workspace_a = await _create_workspace(client, headers, "Cross A")
    workspace_b = await _create_workspace(client, headers, "Cross B")
    create_response = await client.post(
        f"/api/v1/workspaces/{workspace_a}/cases",
        json={"title": "Case in A only"},
        headers=headers,
    )
    case_id = response_data(create_response)["id"]

    detail_response = await client.get(
        f"/api/v1/workspaces/{workspace_b}/cases/{case_id}",
        headers=headers,
    )
    assert detail_response.status_code == 404


async def test_create_case_non_member_returns_404(client: AsyncClient) -> None:
    owner_headers = await auth_headers(
        client,
        f"case-owner-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, owner_headers, "Private Cases")

    other_email = f"case-nonmember-create-{uuid.uuid4()}@example.com"
    await register_user(client, email=other_email)
    other_headers = {
        "Authorization": f"Bearer {await login_user(client, email=other_email)}"
    }
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Forbidden case"},
        headers=other_headers,
    )
    assert response.status_code == 404


async def test_list_cases_non_member_returns_404(client: AsyncClient) -> None:
    owner_headers = await auth_headers(
        client,
        f"case-owner-list-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, owner_headers, "Private List")

    other_email = f"case-nonmember-list-{uuid.uuid4()}@example.com"
    await register_user(client, email=other_email)
    other_headers = {
        "Authorization": f"Bearer {await login_user(client, email=other_email)}"
    }
    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        headers=other_headers,
    )
    assert response.status_code == 404


async def test_get_case_non_member_returns_404(client: AsyncClient) -> None:
    owner_headers = await auth_headers(
        client,
        f"case-owner-detail-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, owner_headers, "Private Detail")
    create_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Hidden case"},
        headers=owner_headers,
    )
    case_id = response_data(create_response)["id"]

    other_email = f"case-nonmember-detail-{uuid.uuid4()}@example.com"
    await register_user(client, email=other_email)
    other_headers = {
        "Authorization": f"Bearer {await login_user(client, email=other_email)}"
    }
    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        headers=other_headers,
    )
    assert response.status_code == 404
