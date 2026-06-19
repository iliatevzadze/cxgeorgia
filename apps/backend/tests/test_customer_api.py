"""Tests for customer record API."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.enums import CustomerStatus
from app.services.customer_service import archive_customer
from tests.conftest import auth_headers, response_data

pytestmark = pytest.mark.asyncio


def _customers_path(workspace_id: str) -> str:
    return f"/api/v1/workspaces/{workspace_id}/customers"


def _customer_detail_path(workspace_id: str, customer_id: str) -> str:
    return f"{_customers_path(workspace_id)}/{customer_id}"


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


async def _create_customer(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: str,
    *,
    display_name: str = "Nino Beridze",
    email: str | None = "nino@example.com",
    external_id: str | None = None,
    status: str | None = None,
) -> dict:
    payload: dict[str, object] = {"display_name": display_name}
    if email is not None:
        payload["email"] = email
    if external_id is not None:
        payload["external_id"] = external_id
    if status is not None:
        payload["status"] = status

    response = await client.post(
        _customers_path(workspace_id),
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201
    return response_data(response)


async def test_list_customers_unauthenticated_returns_401(
    client: AsyncClient,
) -> None:
    response = await client.get(_customers_path(str(uuid.uuid4())))
    assert response.status_code == 401


async def test_create_customer_unauthenticated_returns_401(
    client: AsyncClient,
) -> None:
    response = await client.post(
        _customers_path(str(uuid.uuid4())),
        json={"display_name": "Guest"},
    )
    assert response.status_code == 401


async def test_list_customers_non_member_returns_404(client: AsyncClient) -> None:
    owner_headers = await _auth("cust-owner", client)
    workspace_id = await _create_workspace(client, owner_headers, "Customer Private")
    other_headers = await _auth("cust-other", client)

    response = await client.get(
        _customers_path(workspace_id),
        headers=other_headers,
    )
    assert response.status_code == 404


async def test_create_customer_non_member_returns_404(client: AsyncClient) -> None:
    owner_headers = await _auth("cust-owner-create", client)
    workspace_id = await _create_workspace(
        client,
        owner_headers,
        "Customer Create Private",
    )
    other_headers = await _auth("cust-other-create", client)

    response = await client.post(
        _customers_path(workspace_id),
        json={"display_name": "Blocked"},
        headers=other_headers,
    )
    assert response.status_code == 404


async def test_create_customer_as_active_workspace_member(
    client: AsyncClient,
) -> None:
    headers = await _auth("cust-create", client)
    workspace_id = await _create_workspace(client, headers, "Customer Create")

    data = await _create_customer(
        client,
        headers,
        workspace_id,
        display_name="Giorgi Kvirikashvili",
        email="giorgi@example.com",
        external_id="crm-001",
    )

    assert data["workspace_id"] == workspace_id
    assert data["display_name"] == "Giorgi Kvirikashvili"
    assert data["email"] == "giorgi@example.com"
    assert data["external_id"] == "crm-001"
    assert data["status"] == "active"
    assert data["created_at"]
    assert data["updated_at"]


async def test_list_returns_only_workspace_customers(client: AsyncClient) -> None:
    headers_a = await _auth("cust-list-a", client)
    headers_b = await _auth("cust-list-b", client)
    workspace_a = await _create_workspace(client, headers_a, "Customer List A")
    workspace_b = await _create_workspace(client, headers_b, "Customer List B")

    customer_a = await _create_customer(
        client,
        headers_a,
        workspace_a,
        display_name="Workspace A Customer",
        email="a-customer@example.com",
    )
    await _create_customer(
        client,
        headers_b,
        workspace_b,
        display_name="Workspace B Customer",
        email="b-customer@example.com",
    )

    response = await client.get(
        _customers_path(workspace_a),
        headers=headers_a,
    )
    assert response.status_code == 200
    items = response_data(response)
    assert len(items) == 1
    assert items[0]["id"] == customer_a["id"]
    assert items[0]["display_name"] == "Workspace A Customer"


async def test_get_customer_by_id(client: AsyncClient) -> None:
    headers = await _auth("cust-get", client)
    workspace_id = await _create_workspace(client, headers, "Customer Get")
    created = await _create_customer(
        client,
        headers,
        workspace_id,
        display_name="Detail Customer",
        email="detail@example.com",
    )

    response = await client.get(
        _customer_detail_path(workspace_id, created["id"]),
        headers=headers,
    )
    assert response.status_code == 200
    data = response_data(response)
    assert data["id"] == created["id"]
    assert data["display_name"] == "Detail Customer"


async def test_cross_workspace_customer_access_blocked(
    client: AsyncClient,
) -> None:
    owner_headers = await _auth("cust-cross-owner", client)
    other_headers = await _auth("cust-cross-other", client)
    workspace_id = await _create_workspace(client, owner_headers, "Customer Cross")
    created = await _create_customer(
        client,
        owner_headers,
        workspace_id,
        display_name="Private Customer",
        email="private@example.com",
    )

    response = await client.get(
        _customer_detail_path(workspace_id, created["id"]),
        headers=other_headers,
    )
    assert response.status_code == 404


async def test_update_customer(client: AsyncClient) -> None:
    headers = await _auth("cust-update", client)
    workspace_id = await _create_workspace(client, headers, "Customer Update")
    created = await _create_customer(
        client,
        headers,
        workspace_id,
        display_name="Before Update",
        email="before@example.com",
    )

    response = await client.patch(
        _customer_detail_path(workspace_id, created["id"]),
        json={
            "display_name": "After Update",
            "phone": "+995555123456",
            "notes": "Preferred contact by phone",
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response_data(response)
    assert data["display_name"] == "After Update"
    assert data["phone"] == "+995555123456"
    assert data["notes"] == "Preferred contact by phone"
    assert data["email"] == "before@example.com"


async def test_archive_customer_via_patch(client: AsyncClient) -> None:
    headers = await _auth("cust-archive", client)
    workspace_id = await _create_workspace(client, headers, "Customer Archive")
    created = await _create_customer(
        client,
        headers,
        workspace_id,
        display_name="Archive Customer",
        email="archive@example.com",
    )

    response = await client.patch(
        _customer_detail_path(workspace_id, created["id"]),
        json={"status": "archived"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["status"] == "archived"


async def test_archive_customer_via_service(
    db_session: AsyncSession,
    client: AsyncClient,
) -> None:
    headers = await _auth("cust-archive-service", client)
    workspace_id = await _create_workspace(client, headers, "Customer Archive Service")
    created = await _create_customer(
        client,
        headers,
        workspace_id,
        display_name="Service Archive",
        email="service-archive@example.com",
    )

    customer = await db_session.scalar(
        select(Customer).where(Customer.id == uuid.UUID(created["id"])),
    )
    assert customer is not None
    await archive_customer(db_session, customer.workspace_id, customer.id)
    await db_session.flush()

    response = await client.get(
        _customer_detail_path(workspace_id, created["id"]),
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["status"] == "archived"


async def test_delete_customer_hard_deletes_record(client: AsyncClient) -> None:
    headers = await _auth("cust-delete", client)
    workspace_id = await _create_workspace(client, headers, "Customer Delete")
    created = await _create_customer(
        client,
        headers,
        workspace_id,
        display_name="Delete Customer",
        email="delete@example.com",
    )

    response = await client.delete(
        _customer_detail_path(workspace_id, created["id"]),
        headers=headers,
    )
    assert response.status_code == 200
    data = response_data(response)
    assert data["id"] == created["id"]
    assert data["deleted"] is True

    missing = await client.get(
        _customer_detail_path(workspace_id, created["id"]),
        headers=headers,
    )
    assert missing.status_code == 404


async def test_duplicate_email_in_same_workspace_returns_422(
    client: AsyncClient,
) -> None:
    headers = await _auth("cust-dup-email", client)
    workspace_id = await _create_workspace(client, headers, "Customer Dup Email")
    await _create_customer(
        client,
        headers,
        workspace_id,
        display_name="First",
        email="dup@example.com",
    )

    response = await client.post(
        _customers_path(workspace_id),
        json={"display_name": "Second", "email": "dup@example.com"},
        headers=headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Customer email already exists in this workspace"
    )


async def test_same_email_in_different_workspace_allowed(client: AsyncClient) -> None:
    headers_a = await _auth("cust-email-a", client)
    headers_b = await _auth("cust-email-b", client)
    workspace_a = await _create_workspace(client, headers_a, "Customer Email A")
    workspace_b = await _create_workspace(client, headers_b, "Customer Email B")

    customer_a = await _create_customer(
        client,
        headers_a,
        workspace_a,
        display_name="Shared Email A",
        email="shared@example.com",
    )
    customer_b = await _create_customer(
        client,
        headers_b,
        workspace_b,
        display_name="Shared Email B",
        email="shared@example.com",
    )

    assert customer_a["id"] != customer_b["id"]


async def test_duplicate_external_id_in_same_workspace_returns_422(
    client: AsyncClient,
) -> None:
    headers = await _auth("cust-dup-ext", client)
    workspace_id = await _create_workspace(client, headers, "Customer Dup External")
    await _create_customer(
        client,
        headers,
        workspace_id,
        display_name="First",
        email="first@example.com",
        external_id="crm-100",
    )

    response = await client.post(
        _customers_path(workspace_id),
        json={
            "display_name": "Second",
            "email": "second@example.com",
            "external_id": "crm-100",
        },
        headers=headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Customer external ID already exists in this workspace"
    )


async def test_list_customers_search_filter(client: AsyncClient) -> None:
    headers = await _auth("cust-search", client)
    workspace_id = await _create_workspace(client, headers, "Customer Search")
    await _create_customer(
        client,
        headers,
        workspace_id,
        display_name="Alpha Customer",
        email="alpha@example.com",
    )
    await _create_customer(
        client,
        headers,
        workspace_id,
        display_name="Beta Customer",
        email="beta@example.com",
    )

    response = await client.get(
        _customers_path(workspace_id),
        params={"search": "alpha"},
        headers=headers,
    )
    assert response.status_code == 200
    items = response_data(response)
    assert len(items) == 1
    assert items[0]["display_name"] == "Alpha Customer"


async def test_list_customers_status_filter(client: AsyncClient) -> None:
    headers = await _auth("cust-status-filter", client)
    workspace_id = await _create_workspace(client, headers, "Customer Status Filter")
    active = await _create_customer(
        client,
        headers,
        workspace_id,
        display_name="Active Customer",
        email="active@example.com",
    )
    archived = await _create_customer(
        client,
        headers,
        workspace_id,
        display_name="Archived Customer",
        email="archived@example.com",
    )
    await client.patch(
        _customer_detail_path(workspace_id, archived["id"]),
        json={"status": "archived"},
        headers=headers,
    )

    response = await client.get(
        _customers_path(workspace_id),
        params={"status": "active"},
        headers=headers,
    )
    assert response.status_code == 200
    items = response_data(response)
    assert len(items) == 1
    assert items[0]["id"] == active["id"]
    assert items[0]["status"] == CustomerStatus.ACTIVE.value
