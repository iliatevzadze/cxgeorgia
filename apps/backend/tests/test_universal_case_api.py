"""Tests for Universal Case API."""

import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import (
    CasePriority,
    CaseSource,
    CaseStatus,
    SlaStatus,
    WorkspaceMemberRole,
    WorkspaceMemberStatus,
)
from app.models.universal_case import UniversalCase
from app.models.user import User
from app.models.workspace_membership import WorkspaceMembership
from tests.conftest import (
    auth_headers,
    list_case_items,
    list_cases_page,
    login_user,
    register_user,
    response_data,
)

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


async def _create_case(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: str,
    *,
    title: str = "Patch test case",
    customer_id: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    source: str | None = None,
    assigned_to_user_id: str | None = None,
) -> str:
    payload: dict[str, object] = {"title": title}
    if customer_id is not None:
        payload["customer_id"] = customer_id
    if status is not None:
        payload["status"] = status
    if priority is not None:
        payload["priority"] = priority
    if source is not None:
        payload["source"] = source
    if assigned_to_user_id is not None:
        payload["assigned_to_user_id"] = assigned_to_user_id
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201
    return response_data(response)["id"]


async def _get_user_id(client: AsyncClient, headers: dict[str, str]) -> str:
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    return response_data(response)["id"]


async def _add_active_workspace_member(
    client: AsyncClient,
    db_session: AsyncSession,
    workspace_id: str,
    *,
    email: str,
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


async def _create_customer(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: str,
    *,
    display_name: str = "Linked Customer",
    email: str | None = "linked@example.com",
) -> str:
    payload: dict[str, object] = {"display_name": display_name}
    if email is not None:
        payload["email"] = email
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/customers",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201
    return response_data(response)["id"]


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
    items = list_case_items(list_response)
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
    items = list_case_items(list_response)
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
    items = list_case_items(list_response)
    assert [item["id"] for item in items] == [second_id, first_id]


async def test_list_cases_without_customer_id_returns_all_workspace_cases(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-list-all-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "All Cases Workspace")
    customer_a_id = await _create_customer(
        client,
        headers,
        workspace_id,
        display_name="Customer A",
        email="customer-a@example.com",
    )
    customer_b_id = await _create_customer(
        client,
        headers,
        workspace_id,
        display_name="Customer B",
        email="customer-b@example.com",
    )
    linked_a_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Linked to A",
        customer_id=customer_a_id,
    )
    linked_b_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Linked to B",
        customer_id=customer_b_id,
    )
    unlinked_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Unlinked case",
    )

    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        headers=headers,
    )
    assert list_response.status_code == 200
    items = list_case_items(list_response)
    assert {item["id"] for item in items} == {
        linked_a_id,
        linked_b_id,
        unlinked_id,
    }


async def test_list_cases_with_valid_customer_id_returns_only_linked_cases(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-list-filter-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Filter Workspace")
    customer_id = await _create_customer(client, headers, workspace_id)
    linked_case_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Customer case",
        customer_id=customer_id,
    )
    await _create_case(client, headers, workspace_id, title="Unlinked case")

    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"customer_id": customer_id},
        headers=headers,
    )
    assert list_response.status_code == 200
    items = list_case_items(list_response)
    assert len(items) == 1
    assert items[0]["id"] == linked_case_id
    assert items[0]["customer_id"] == customer_id


async def test_list_cases_with_customer_id_excludes_other_customer_cases(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-list-exclude-other-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Exclude Other Workspace")
    customer_a_id = await _create_customer(
        client,
        headers,
        workspace_id,
        display_name="Filter Customer",
        email="filter-customer@example.com",
    )
    customer_b_id = await _create_customer(
        client,
        headers,
        workspace_id,
        display_name="Other Customer",
        email="other-customer@example.com",
    )
    linked_a_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Case for filter customer",
        customer_id=customer_a_id,
    )
    await _create_case(
        client,
        headers,
        workspace_id,
        title="Case for other customer",
        customer_id=customer_b_id,
    )

    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"customer_id": customer_a_id},
        headers=headers,
    )
    assert list_response.status_code == 200
    items = list_case_items(list_response)
    assert len(items) == 1
    assert items[0]["id"] == linked_a_id


async def test_list_cases_with_customer_id_excludes_unlinked_cases(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-list-exclude-unlinked-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Exclude Unlinked Workspace",
    )
    customer_id = await _create_customer(client, headers, workspace_id)
    linked_case_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Linked only",
        customer_id=customer_id,
    )
    await _create_case(client, headers, workspace_id, title="No customer")

    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"customer_id": customer_id},
        headers=headers,
    )
    assert list_response.status_code == 200
    items = list_case_items(list_response)
    assert len(items) == 1
    assert items[0]["id"] == linked_case_id


async def test_list_cases_with_cross_workspace_customer_id_blocked(
    client: AsyncClient,
) -> None:
    owner_headers = await auth_headers(
        client,
        f"case-list-cross-owner-{uuid.uuid4()}@example.com",
    )
    other_headers = await auth_headers(
        client,
        f"case-list-cross-other-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        owner_headers,
        "List Cross Workspace",
    )
    other_workspace_id = await _create_workspace(
        client,
        other_headers,
        "Other List Workspace",
    )
    other_customer_id = await _create_customer(
        client,
        other_headers,
        other_workspace_id,
        email="list-cross@example.com",
    )

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"customer_id": other_customer_id},
        headers=owner_headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Customer must belong to this workspace"


async def test_list_cases_with_customer_id_unauthenticated_returns_401(
    client: AsyncClient,
) -> None:
    response = await client.get(
        f"/api/v1/workspaces/{uuid.uuid4()}/cases",
        params={"customer_id": str(uuid.uuid4())},
    )
    assert response.status_code == 401


async def test_list_cases_with_customer_id_non_member_returns_404(
    client: AsyncClient,
) -> None:
    owner_headers = await auth_headers(
        client,
        f"case-owner-list-filter-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, owner_headers, "Private Filter List")
    customer_id = await _create_customer(client, owner_headers, workspace_id)

    other_email = f"case-nonmember-list-filter-{uuid.uuid4()}@example.com"
    await register_user(client, email=other_email)
    other_headers = {
        "Authorization": f"Bearer {await login_user(client, email=other_email)}"
    }
    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"customer_id": customer_id},
        headers=other_headers,
    )
    assert response.status_code == 404


async def test_list_cases_filter_by_status(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-list-status-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Status Filter Workspace")
    open_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Open case",
        status=CaseStatus.OPEN.value,
    )
    await _create_case(
        client,
        headers,
        workspace_id,
        title="Pending case",
        status=CaseStatus.PENDING.value,
    )

    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"status": CaseStatus.OPEN.value},
        headers=headers,
    )
    assert list_response.status_code == 200
    items = list_case_items(list_response)
    assert len(items) == 1
    assert items[0]["id"] == open_id


async def test_list_cases_filter_by_priority(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-list-priority-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Priority Filter Workspace")
    high_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="High priority",
        priority=CasePriority.HIGH.value,
    )
    await _create_case(
        client,
        headers,
        workspace_id,
        title="Normal priority",
        priority=CasePriority.NORMAL.value,
    )

    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"priority": CasePriority.HIGH.value},
        headers=headers,
    )
    assert list_response.status_code == 200
    items = list_case_items(list_response)
    assert len(items) == 1
    assert items[0]["id"] == high_id


async def test_list_cases_filter_by_source(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-list-source-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Source Filter Workspace")
    email_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Email case",
        source=CaseSource.EMAIL.value,
    )
    await _create_case(
        client,
        headers,
        workspace_id,
        title="Manual case",
        source=CaseSource.MANUAL.value,
    )

    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"source": CaseSource.EMAIL.value},
        headers=headers,
    )
    assert list_response.status_code == 200
    items = list_case_items(list_response)
    assert len(items) == 1
    assert items[0]["id"] == email_id


async def test_list_cases_filter_by_assigned_to_user_id(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-list-assignee-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Assignee Filter Workspace")
    user_id = await _get_user_id(client, headers)
    assigned_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Assigned case",
        assigned_to_user_id=user_id,
    )
    await _create_case(client, headers, workspace_id, title="Unassigned case")

    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"assigned_to_user_id": user_id},
        headers=headers,
    )
    assert list_response.status_code == 200
    items = list_case_items(list_response)
    assert len(items) == 1
    assert items[0]["id"] == assigned_id


async def test_list_cases_filter_by_sla_status(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    suffix = uuid.uuid4().hex[:12]
    headers = await auth_headers(client, f"case-list-sla-{suffix}@example.com")
    workspace_id = await _create_workspace(client, headers, "SLA Filter Workspace")
    user = await db_session.scalar(
        select(User).where(User.email == f"case-list-sla-{suffix}@example.com")
    )
    assert user is not None

    at_risk_case = UniversalCase(
        workspace_id=UUID(workspace_id),
        title="At risk case",
        status=CaseStatus.OPEN,
        sla_status=SlaStatus.AT_RISK,
        created_by_user_id=user.id,
    )
    on_track_case = UniversalCase(
        workspace_id=UUID(workspace_id),
        title="On track case",
        status=CaseStatus.OPEN,
        sla_status=SlaStatus.ON_TRACK,
        created_by_user_id=user.id,
    )
    db_session.add_all([at_risk_case, on_track_case])
    await db_session.flush()

    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"sla_status": SlaStatus.AT_RISK.value},
        headers=headers,
    )
    assert list_response.status_code == 200
    items = list_case_items(list_response)
    assert len(items) == 1
    assert items[0]["id"] == str(at_risk_case.id)


async def test_list_cases_combine_status_and_priority_filters(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-list-combo-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Combo Filter Workspace")
    match_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Open high",
        status=CaseStatus.OPEN.value,
        priority=CasePriority.HIGH.value,
    )
    await _create_case(
        client,
        headers,
        workspace_id,
        title="Open normal",
        status=CaseStatus.OPEN.value,
        priority=CasePriority.NORMAL.value,
    )
    await _create_case(
        client,
        headers,
        workspace_id,
        title="Pending high",
        status=CaseStatus.PENDING.value,
        priority=CasePriority.HIGH.value,
    )

    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={
            "status": CaseStatus.OPEN.value,
            "priority": CasePriority.HIGH.value,
        },
        headers=headers,
    )
    assert list_response.status_code == 200
    items = list_case_items(list_response)
    assert len(items) == 1
    assert items[0]["id"] == match_id


async def test_list_cases_combine_customer_id_and_status_filters(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-list-customer-status-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Customer Status Filter Workspace",
    )
    customer_id = await _create_customer(client, headers, workspace_id)
    match_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Linked open",
        customer_id=customer_id,
        status=CaseStatus.OPEN.value,
    )
    await _create_case(
        client,
        headers,
        workspace_id,
        title="Linked pending",
        customer_id=customer_id,
        status=CaseStatus.PENDING.value,
    )
    await _create_case(
        client,
        headers,
        workspace_id,
        title="Unlinked open",
        status=CaseStatus.OPEN.value,
    )

    list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={
            "customer_id": customer_id,
            "status": CaseStatus.OPEN.value,
        },
        headers=headers,
    )
    assert list_response.status_code == 200
    items = list_case_items(list_response)
    assert len(items) == 1
    assert items[0]["id"] == match_id


async def test_list_cases_assigned_to_user_id_outside_workspace_blocked(
    client: AsyncClient,
) -> None:
    owner_headers = await auth_headers(
        client,
        f"case-list-assign-outside-owner-{uuid.uuid4()}@example.com",
    )
    other_email = f"case-list-assign-outside-other-{uuid.uuid4()}@example.com"
    workspace_id = await _create_workspace(
        client,
        owner_headers,
        "Assign Outside List Workspace",
    )
    other_headers = await auth_headers(client, other_email)
    other_user_id = await _get_user_id(client, other_headers)
    await _create_workspace(client, other_headers, "Other Assign Workspace")

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"assigned_to_user_id": other_user_id},
        headers=owner_headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Assignee must be an active member of this workspace"
    )


async def test_list_cases_invalid_enum_query_values_return_422(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-list-invalid-enum-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Invalid Enum Workspace")

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"status": "not-a-status"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_list_cases_with_filters_unauthenticated_returns_401(
    client: AsyncClient,
) -> None:
    response = await client.get(
        f"/api/v1/workspaces/{uuid.uuid4()}/cases",
        params={"status": CaseStatus.OPEN.value},
    )
    assert response.status_code == 401


async def test_list_cases_with_filters_non_member_returns_404(
    client: AsyncClient,
) -> None:
    owner_headers = await auth_headers(
        client,
        f"case-owner-list-filters-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        owner_headers,
        "Private Filter List Workspace",
    )

    other_email = f"case-nonmember-list-filters-{uuid.uuid4()}@example.com"
    await register_user(client, email=other_email)
    other_headers = {
        "Authorization": f"Bearer {await login_user(client, email=other_email)}"
    }
    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"priority": CasePriority.HIGH.value},
        headers=other_headers,
    )
    assert response.status_code == 404


async def test_list_cases_without_explicit_pagination_returns_default_metadata(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-list-default-page-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Default Page Workspace")
    await _create_case(client, headers, workspace_id, title="Paged case")

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        headers=headers,
    )
    assert response.status_code == 200
    page = list_cases_page(response)
    assert page["limit"] == 50
    assert page["offset"] == 0
    assert page["total"] == 1
    assert len(page["items"]) == 1


async def test_list_cases_limit_returns_only_requested_number(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-list-limit-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Limit Workspace")
    for index in range(3):
        await _create_case(
            client,
            headers,
            workspace_id,
            title=f"Limit case {index}",
        )

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"limit": 2},
        headers=headers,
    )
    assert response.status_code == 200
    page = list_cases_page(response)
    assert len(page["items"]) == 2
    assert page["total"] == 3
    assert page["limit"] == 2
    assert page["offset"] == 0


async def test_list_cases_offset_skips_earlier_cases(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"case-list-offset-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Offset Workspace")
    first_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Offset first",
    )
    second_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Offset second",
    )
    first_case = await db_session.get(UniversalCase, UUID(first_id))
    assert first_case is not None
    first_case.created_at = datetime.now(UTC) - timedelta(hours=1)
    await db_session.flush()

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"limit": 1, "offset": 1},
        headers=headers,
    )
    assert response.status_code == 200
    page = list_cases_page(response)
    assert page["total"] == 2
    assert len(page["items"]) == 1
    assert page["items"][0]["id"] == first_id
    assert second_id != first_id


async def test_list_cases_limit_and_offset_preserve_newest_first_order(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"case-list-page-order-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Page Order Workspace")
    older_id = await _create_case(client, headers, workspace_id, title="Older case")
    newest_id = await _create_case(client, headers, workspace_id, title="Newer case")
    older_case = await db_session.get(UniversalCase, UUID(older_id))
    assert older_case is not None
    older_case.created_at = datetime.now(UTC) - timedelta(hours=1)
    await db_session.flush()

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"limit": 1, "offset": 0},
        headers=headers,
    )
    assert response.status_code == 200
    page = list_cases_page(response)
    assert len(page["items"]) == 1
    assert page["items"][0]["id"] == newest_id


async def test_list_cases_excessive_limit_returns_422(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-list-max-limit-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Max Limit Workspace")

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"limit": 101},
        headers=headers,
    )
    assert response.status_code == 422


async def test_list_cases_negative_offset_returns_422(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-list-negative-offset-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Negative Offset Workspace")

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"offset": -1},
        headers=headers,
    )
    assert response.status_code == 422


async def test_list_cases_zero_limit_returns_422(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-list-zero-limit-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Zero Limit Workspace")

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"limit": 0},
        headers=headers,
    )
    assert response.status_code == 422


async def test_list_cases_negative_limit_returns_422(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-list-negative-limit-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Negative Limit Workspace")

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"limit": -1},
        headers=headers,
    )
    assert response.status_code == 422


async def test_list_cases_pagination_combines_with_status_filter(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-list-page-status-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Page Status Workspace")
    open_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Open for page",
        status=CaseStatus.OPEN.value,
    )
    await _create_case(
        client,
        headers,
        workspace_id,
        title="Pending for page",
        status=CaseStatus.PENDING.value,
    )

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"status": CaseStatus.OPEN.value, "limit": 1},
        headers=headers,
    )
    assert response.status_code == 200
    page = list_cases_page(response)
    assert page["total"] == 1
    assert len(page["items"]) == 1
    assert page["items"][0]["id"] == open_id


async def test_list_cases_pagination_combines_with_customer_id_filter(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-list-page-customer-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Page Customer Workspace")
    customer_id = await _create_customer(client, headers, workspace_id)
    linked_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Linked for page",
        customer_id=customer_id,
    )
    await _create_case(client, headers, workspace_id, title="Unlinked for page")

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"customer_id": customer_id, "limit": 1},
        headers=headers,
    )
    assert response.status_code == 200
    page = list_cases_page(response)
    assert page["total"] == 1
    assert len(page["items"]) == 1
    assert page["items"][0]["id"] == linked_id


async def test_list_cases_with_pagination_unauthenticated_returns_401(
    client: AsyncClient,
) -> None:
    response = await client.get(
        f"/api/v1/workspaces/{uuid.uuid4()}/cases",
        params={"limit": 10, "offset": 0},
    )
    assert response.status_code == 401


async def test_list_cases_with_pagination_non_member_returns_404(
    client: AsyncClient,
) -> None:
    owner_headers = await auth_headers(
        client,
        f"case-owner-list-page-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, owner_headers, "Private Page List")

    other_email = f"case-nonmember-list-page-{uuid.uuid4()}@example.com"
    await register_user(client, email=other_email)
    other_headers = {
        "Authorization": f"Bearer {await login_user(client, email=other_email)}"
    }
    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        params={"limit": 10, "offset": 0},
        headers=other_headers,
    )
    assert response.status_code == 404


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


async def test_patch_case_unauthenticated_returns_401(client: AsyncClient) -> None:
    response = await client.patch(
        f"/api/v1/workspaces/{uuid.uuid4()}/cases/{uuid.uuid4()}",
        json={"status": "pending"},
    )
    assert response.status_code == 401


async def test_patch_case_status_as_workspace_member(client: AsyncClient) -> None:
    email = f"case-patch-status-{uuid.uuid4()}@example.com"
    headers = await auth_headers(client, email)
    workspace_id = await _create_workspace(client, headers, "Patch Status Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"status": "pending"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["status"] == CaseStatus.PENDING.value


async def test_patch_case_priority_as_workspace_member(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-priority-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Priority Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"priority": "high"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["priority"] == CasePriority.HIGH.value


async def test_patch_case_status_and_priority_together(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"case-patch-both-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Patch Both Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"status": "resolved", "priority": "urgent"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response_data(response)
    assert data["status"] == CaseStatus.RESOLVED.value
    assert data["priority"] == CasePriority.URGENT.value


async def test_patch_case_persists_changes(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    email = f"case-patch-persist-{uuid.uuid4()}@example.com"
    headers = await auth_headers(client, email)
    workspace_id = await _create_workspace(client, headers, "Patch Persist Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"status": "closed"},
        headers=headers,
    )
    assert response.status_code == 200

    case = await db_session.get(UniversalCase, UUID(case_id))
    assert case is not None
    assert case.status == CaseStatus.CLOSED


async def test_patch_case_cross_workspace_returns_404(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"case-patch-cross-{uuid.uuid4()}@example.com")
    workspace_a = await _create_workspace(client, headers, "Patch Cross A")
    workspace_b = await _create_workspace(client, headers, "Patch Cross B")
    case_id = await _create_case(client, headers, workspace_a)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_b}/cases/{case_id}",
        json={"status": "pending"},
        headers=headers,
    )
    assert response.status_code == 404


async def test_patch_case_non_member_returns_404(client: AsyncClient) -> None:
    owner_headers = await auth_headers(
        client,
        f"case-patch-owner-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, owner_headers, "Patch Private")
    case_id = await _create_case(client, owner_headers, workspace_id)

    other_email = f"case-patch-nonmember-{uuid.uuid4()}@example.com"
    await register_user(client, email=other_email)
    other_headers = {
        "Authorization": f"Bearer {await login_user(client, email=other_email)}"
    }
    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"status": "pending"},
        headers=other_headers,
    )
    assert response.status_code == 404


async def test_patch_case_invalid_status_returns_422(client: AsyncClient) -> None:
    email = f"case-patch-bad-status-{uuid.uuid4()}@example.com"
    headers = await auth_headers(client, email)
    workspace_id = await _create_workspace(client, headers, "Patch Bad Status")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"status": "not-a-status"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_patch_case_invalid_priority_returns_422(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-bad-priority-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Bad Priority")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"priority": "not-a-priority"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_patch_case_empty_body_returns_422(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"case-patch-empty-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Patch Empty Body")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={},
        headers=headers,
    )
    assert response.status_code == 422


async def test_patch_case_forbidden_fields_return_422(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-forbidden-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Forbidden")
    case_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Original title",
    )

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={
            "status": "pending",
            "id": str(uuid.uuid4()),
            "workspace_id": str(uuid.uuid4()),
            "created_by_user_id": str(uuid.uuid4()),
            "created_at": "2020-01-01T00:00:00+00:00",
            "updated_at": "2020-01-01T00:00:00+00:00",
        },
        headers=headers,
    )
    assert response.status_code == 422

    detail_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        headers=headers,
    )
    assert response_data(detail_response)["title"] == "Original title"
    assert response_data(detail_response)["status"] == CaseStatus.OPEN.value


async def test_patch_case_title_only_as_workspace_member(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"case-patch-title-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Patch Title Workspace")
    case_id = await _create_case(client, headers, workspace_id, title="Old title")

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"title": "New title"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["title"] == "New title"


async def test_patch_case_title_is_trimmed(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"case-patch-trim-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Patch Trim Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"title": "  Trimmed title  "},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["title"] == "Trimmed title"


async def test_patch_case_whitespace_only_title_returns_422(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-blank-title-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Blank Title")
    case_id = await _create_case(client, headers, workspace_id, title="Keep title")

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"title": "   "},
        headers=headers,
    )
    assert response.status_code == 422

    detail_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        headers=headers,
    )
    assert response_data(detail_response)["title"] == "Keep title"


async def test_patch_case_description_only_as_workspace_member(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-desc-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Desc Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"description": "Updated description"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["description"] == "Updated description"


async def test_patch_case_clear_description_with_null(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-null-desc-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Null Desc")

    create_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Case with description", "description": "Initial text"},
        headers=headers,
    )
    assert create_response.status_code == 201
    case_id = response_data(create_response)["id"]

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"description": None},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["description"] is None


async def test_patch_case_title_and_description_together(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-title-desc-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Title Desc")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"title": "Combined title", "description": "Combined description"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response_data(response)
    assert data["title"] == "Combined title"
    assert data["description"] == "Combined description"


async def test_patch_case_title_description_status_and_priority_together(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-all-fields-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch All Fields")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={
            "title": "Full update title",
            "description": "Full update description",
            "status": "resolved",
            "priority": "high",
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response_data(response)
    assert data["title"] == "Full update title"
    assert data["description"] == "Full update description"
    assert data["status"] == CaseStatus.RESOLVED.value
    assert data["priority"] == CasePriority.HIGH.value


async def test_patch_case_source_only_as_workspace_member(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-source-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Source Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"source": "email"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["source"] == CaseSource.EMAIL.value


async def test_patch_case_invalid_source_returns_422(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-bad-source-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Bad Source")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"source": "not-a-source"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_patch_case_source_null_returns_422(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-null-source-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Null Source")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"source": None},
        headers=headers,
    )
    assert response.status_code == 422


async def test_patch_case_customer_name_only_as_workspace_member(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-cust-name-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Customer Name")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"customer_name": "Nino Beridze"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["customer_name"] == "Nino Beridze"


async def test_patch_case_customer_email_only_as_workspace_member(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-cust-email-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Customer Email")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"customer_email": "nino@example.com"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["customer_email"] == "nino@example.com"


async def test_patch_case_external_reference_only_as_workspace_member(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-ext-ref-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch External Ref")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"external_reference": "EXT-42"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["external_reference"] == "EXT-42"


async def test_patch_case_customer_name_is_trimmed(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-trim-name-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Trim Name")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"customer_name": "  Trimmed Name  "},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["customer_name"] == "Trimmed Name"


async def test_patch_case_customer_email_is_trimmed(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-trim-email-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Trim Email")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"customer_email": "  trim@example.com  "},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["customer_email"] == "trim@example.com"


async def test_patch_case_external_reference_is_trimmed(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-trim-ref-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Trim Ref")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"external_reference": "  EXT-99  "},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["external_reference"] == "EXT-99"


async def test_patch_case_empty_customer_name_clears_to_null(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-empty-name-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Empty Name")
    create_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Case", "customer_name": "Existing name"},
        headers=headers,
    )
    assert create_response.status_code == 201
    case_id = response_data(create_response)["id"]

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"customer_name": "   "},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["customer_name"] is None


async def test_patch_case_empty_customer_email_clears_to_null(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-empty-email-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Empty Email")
    create_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Case", "customer_email": "keep@example.com"},
        headers=headers,
    )
    assert create_response.status_code == 201
    case_id = response_data(create_response)["id"]

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"customer_email": ""},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["customer_email"] is None


async def test_patch_case_empty_external_reference_clears_to_null(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-empty-ref-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Empty Ref")
    create_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Case", "external_reference": "EXT-OLD"},
        headers=headers,
    )
    assert create_response.status_code == 201
    case_id = response_data(create_response)["id"]

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"external_reference": "  "},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["external_reference"] is None


async def test_patch_case_clear_customer_name_with_null(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-null-name-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Null Name")
    create_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Case", "customer_name": "Existing name"},
        headers=headers,
    )
    assert create_response.status_code == 201
    case_id = response_data(create_response)["id"]

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"customer_name": None},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["customer_name"] is None


async def test_patch_case_clear_customer_email_with_null(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-null-email-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Null Email")
    create_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Case", "customer_email": "keep@example.com"},
        headers=headers,
    )
    assert create_response.status_code == 201
    case_id = response_data(create_response)["id"]

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"customer_email": None},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["customer_email"] is None


async def test_patch_case_clear_external_reference_with_null(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-null-ref-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Null Ref")
    create_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Case", "external_reference": "EXT-OLD"},
        headers=headers,
    )
    assert create_response.status_code == 201
    case_id = response_data(create_response)["id"]

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"external_reference": None},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["external_reference"] is None


async def test_patch_case_source_and_customer_metadata_together(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-source-customer-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Source Customer")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={
            "source": "phone",
            "customer_name": "Giorgi",
            "customer_email": "giorgi@example.com",
            "external_reference": "EXT-100",
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response_data(response)
    assert data["source"] == CaseSource.PHONE.value
    assert data["customer_name"] == "Giorgi"
    assert data["customer_email"] == "giorgi@example.com"
    assert data["external_reference"] == "EXT-100"


async def test_patch_case_all_allowed_fields_together(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-all-allowed-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch All Allowed")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={
            "title": "Full case title",
            "description": "Full case description",
            "status": "pending",
            "priority": "urgent",
            "source": "web",
            "customer_name": "Mariam",
            "customer_email": "mariam@example.com",
            "external_reference": "EXT-FULL",
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response_data(response)
    assert data["title"] == "Full case title"
    assert data["description"] == "Full case description"
    assert data["status"] == CaseStatus.PENDING.value
    assert data["priority"] == CasePriority.URGENT.value
    assert data["source"] == CaseSource.WEB.value
    assert data["customer_name"] == "Mariam"
    assert data["customer_email"] == "mariam@example.com"
    assert data["external_reference"] == "EXT-FULL"


async def test_patch_case_assign_to_self(client: AsyncClient) -> None:
    email = f"case-patch-assign-self-{uuid.uuid4()}@example.com"
    headers = await auth_headers(client, email)
    workspace_id = await _create_workspace(client, headers, "Assign Self Workspace")
    case_id = await _create_case(client, headers, workspace_id)
    user_id = await _get_user_id(client, headers)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"assigned_to_user_id": user_id},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["assigned_to_user_id"] == user_id


async def test_patch_case_assign_to_other_active_member(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_email = f"case-patch-assign-owner-{uuid.uuid4()}@example.com"
    member_email = f"case-patch-assign-member-{uuid.uuid4()}@example.com"
    headers = await auth_headers(client, owner_email)
    workspace_id = await _create_workspace(client, headers, "Assign Member Workspace")
    case_id = await _create_case(client, headers, workspace_id)
    member_user_id = await _add_active_workspace_member(
        client,
        db_session,
        workspace_id,
        email=member_email,
    )

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"assigned_to_user_id": member_user_id},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["assigned_to_user_id"] == member_user_id


async def test_patch_case_unassign_with_null(client: AsyncClient) -> None:
    email = f"case-patch-unassign-{uuid.uuid4()}@example.com"
    headers = await auth_headers(client, email)
    workspace_id = await _create_workspace(client, headers, "Unassign Workspace")
    case_id = await _create_case(client, headers, workspace_id)
    user_id = await _get_user_id(client, headers)

    assign_response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"assigned_to_user_id": user_id},
        headers=headers,
    )
    assert assign_response.status_code == 200
    assert response_data(assign_response)["assigned_to_user_id"] == user_id

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"assigned_to_user_id": None},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["assigned_to_user_id"] is None


async def test_patch_case_assignment_persists_in_database(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    email = f"case-patch-assign-persist-{uuid.uuid4()}@example.com"
    headers = await auth_headers(client, email)
    workspace_id = await _create_workspace(client, headers, "Assign Persist Workspace")
    case_id = await _create_case(client, headers, workspace_id)
    user_id = await _get_user_id(client, headers)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"assigned_to_user_id": user_id},
        headers=headers,
    )
    assert response.status_code == 200

    case = await db_session.get(UniversalCase, UUID(case_id))
    assert case is not None
    assert str(case.assigned_to_user_id) == user_id


async def test_patch_case_invalid_assigned_to_user_id_format_returns_422(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-assign-bad-uuid-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Assign Bad UUID Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"assigned_to_user_id": "not-a-uuid"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_patch_case_assign_user_outside_workspace_returns_422(
    client: AsyncClient,
) -> None:
    owner_email = f"case-patch-assign-outside-owner-{uuid.uuid4()}@example.com"
    other_email = f"case-patch-assign-outside-other-{uuid.uuid4()}@example.com"
    owner_headers = await auth_headers(client, owner_email)
    workspace_id = await _create_workspace(
        client,
        owner_headers,
        "Assign Outside Workspace",
    )
    case_id = await _create_case(client, owner_headers, workspace_id)

    other_headers = await auth_headers(client, other_email)
    other_user_id = await _get_user_id(client, other_headers)
    await _create_workspace(client, other_headers, "Other User Workspace")

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"assigned_to_user_id": other_user_id},
        headers=owner_headers,
    )
    assert response.status_code == 422


async def test_patch_case_assign_nonexistent_user_returns_422(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-assign-missing-user-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Assign Missing User Workspace",
    )
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"assigned_to_user_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert response.status_code == 422


async def test_patch_case_assign_inactive_member_returns_422(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_email = f"case-patch-assign-inactive-owner-{uuid.uuid4()}@example.com"
    member_email = f"case-patch-assign-inactive-member-{uuid.uuid4()}@example.com"
    owner_headers = await auth_headers(client, owner_email)
    workspace_id = await _create_workspace(
        client,
        owner_headers,
        "Assign Inactive Workspace",
    )
    case_id = await _create_case(client, owner_headers, workspace_id)
    member_user_id = await _add_active_workspace_member(
        client,
        db_session,
        workspace_id,
        email=member_email,
    )
    membership = await db_session.scalar(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == UUID(workspace_id),
            WorkspaceMembership.user_id == UUID(member_user_id),
        )
    )
    assert membership is not None
    membership.status = WorkspaceMemberStatus.REMOVED
    await db_session.flush()

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"assigned_to_user_id": member_user_id},
        headers=owner_headers,
    )
    assert response.status_code == 422


async def test_patch_case_assigned_to_user_id_is_allowed(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-assign-allowed-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Assign Allowed Workspace")
    case_id = await _create_case(client, headers, workspace_id)
    user_id = await _get_user_id(client, headers)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"assigned_to_user_id": user_id},
        headers=headers,
    )
    assert response.status_code == 200


async def test_delete_case_unauthenticated_returns_401(client: AsyncClient) -> None:
    response = await client.delete(
        f"/api/v1/workspaces/{uuid.uuid4()}/cases/{uuid.uuid4()}",
    )
    assert response.status_code == 401


async def test_delete_case_as_workspace_member(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"case-delete-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Delete Case Workspace")
    case_id = await _create_case(client, headers, workspace_id, title="Delete me")

    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response_data(response)
    assert data["id"] == case_id
    assert data["deleted"] is True


async def test_delete_case_get_detail_returns_404_after_delete(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-delete-detail-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Delete Detail Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    delete_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        headers=headers,
    )
    assert delete_response.status_code == 200

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        headers=headers,
    )
    assert response.status_code == 404


async def test_delete_case_list_excludes_deleted_case(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"case-delete-list-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Delete List Workspace")
    case_id = await _create_case(client, headers, workspace_id, title="Listed case")
    other_case_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Remaining case",
    )

    delete_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        headers=headers,
    )
    assert delete_response.status_code == 200

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases",
        headers=headers,
    )
    assert response.status_code == 200
    items = list_case_items(response)
    ids = {item["id"] for item in items}
    assert case_id not in ids
    assert other_case_id in ids


async def test_delete_case_not_found_returns_404(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-delete-missing-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Delete Missing Workspace")

    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/cases/{uuid.uuid4()}",
        headers=headers,
    )
    assert response.status_code == 404


async def test_delete_case_cross_workspace_returns_404(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-delete-cross-{uuid.uuid4()}@example.com",
    )
    workspace_a = await _create_workspace(client, headers, "Delete Cross A")
    workspace_b = await _create_workspace(client, headers, "Delete Cross B")
    case_id = await _create_case(client, headers, workspace_a)

    response = await client.delete(
        f"/api/v1/workspaces/{workspace_b}/cases/{case_id}",
        headers=headers,
    )
    assert response.status_code == 404

    detail_response = await client.get(
        f"/api/v1/workspaces/{workspace_a}/cases/{case_id}",
        headers=headers,
    )
    assert detail_response.status_code == 200


async def test_delete_case_non_member_returns_404(client: AsyncClient) -> None:
    owner_headers = await auth_headers(
        client,
        f"case-delete-owner-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, owner_headers, "Delete Private")
    case_id = await _create_case(client, owner_headers, workspace_id)

    other_email = f"case-delete-nonmember-{uuid.uuid4()}@example.com"
    await register_user(client, email=other_email)
    other_headers = {
        "Authorization": f"Bearer {await login_user(client, email=other_email)}"
    }
    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        headers=other_headers,
    )
    assert response.status_code == 404


async def test_delete_case_does_not_delete_other_case_in_workspace(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"case-delete-other-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Delete Other Workspace")
    case_to_delete = await _create_case(
        client,
        headers,
        workspace_id,
        title="Delete this",
    )
    remaining_case_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Keep this",
    )

    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_to_delete}",
        headers=headers,
    )
    assert response.status_code == 200

    detail_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases/{remaining_case_id}",
        headers=headers,
    )
    assert detail_response.status_code == 200
    assert response_data(detail_response)["title"] == "Keep this"


async def test_create_case_without_customer_still_works(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"case-no-customer-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "No Customer Case")
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Unlinked case"},
        headers=headers,
    )
    assert response.status_code == 201
    assert response_data(response)["customer_id"] is None


async def test_create_case_with_valid_customer_id(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-with-customer-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Linked Case Create")
    customer_id = await _create_customer(client, headers, workspace_id)

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Linked case", "customer_id": customer_id},
        headers=headers,
    )
    assert response.status_code == 201
    data = response_data(response)
    assert data["customer_id"] == customer_id


async def test_create_case_with_cross_workspace_customer_id_blocked(
    client: AsyncClient,
) -> None:
    owner_headers = await auth_headers(
        client,
        f"case-cross-customer-owner-{uuid.uuid4()}@example.com",
    )
    other_headers = await auth_headers(
        client,
        f"case-cross-customer-other-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, owner_headers, "Case Customer Cross")
    other_workspace_id = await _create_workspace(
        client,
        other_headers,
        "Other Customer Workspace",
    )
    other_customer_id = await _create_customer(
        client,
        other_headers,
        other_workspace_id,
        email="other-ws@example.com",
    )

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Blocked link", "customer_id": other_customer_id},
        headers=owner_headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Customer must belong to this workspace"


async def test_patch_case_to_valid_customer_id(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"case-patch-link-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Patch Link Customer")
    customer_id = await _create_customer(client, headers, workspace_id)
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"customer_id": customer_id},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["customer_id"] == customer_id


async def test_patch_case_to_null_unlinks_customer(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"case-patch-unlink-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Patch Unlink Customer")
    customer_id = await _create_customer(client, headers, workspace_id)
    case_id = await _create_case(
        client,
        headers,
        workspace_id,
        title="Linked for unlink",
    )

    link_response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"customer_id": customer_id},
        headers=headers,
    )
    assert link_response.status_code == 200
    assert response_data(link_response)["customer_id"] == customer_id

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"customer_id": None},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["customer_id"] is None


async def test_patch_case_to_cross_workspace_customer_id_blocked(
    client: AsyncClient,
) -> None:
    owner_headers = await auth_headers(
        client,
        f"case-patch-cross-customer-owner-{uuid.uuid4()}@example.com",
    )
    other_headers = await auth_headers(
        client,
        f"case-patch-cross-customer-other-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        owner_headers,
        "Patch Customer Cross",
    )
    other_workspace_id = await _create_workspace(
        client,
        other_headers,
        "Patch Other Customer Workspace",
    )
    other_customer_id = await _create_customer(
        client,
        other_headers,
        other_workspace_id,
        email="patch-other@example.com",
    )
    case_id = await _create_case(client, owner_headers, workspace_id)

    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        json={"customer_id": other_customer_id},
        headers=owner_headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Customer must belong to this workspace"


async def test_deleting_customer_sets_case_customer_id_to_null(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"case-delete-customer-null-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Delete Customer Null FK")
    customer_id = await _create_customer(client, headers, workspace_id)
    create_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Case with customer", "customer_id": customer_id},
        headers=headers,
    )
    assert create_response.status_code == 201
    case_id = response_data(create_response)["id"]

    delete_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/customers/{customer_id}",
        headers=headers,
    )
    assert delete_response.status_code == 200

    case = await db_session.get(UniversalCase, UUID(case_id))
    assert case is not None
    assert case.customer_id is None
