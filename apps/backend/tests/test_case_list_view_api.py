"""Tests for saved case list view API."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_list_view import CaseListView
from tests.conftest import auth_headers, login_user, register_user, response_data

pytestmark = pytest.mark.asyncio


def _views_path(workspace_id: str) -> str:
    return f"/api/v1/workspaces/{workspace_id}/case-list-views"


def _view_detail_path(workspace_id: str, view_id: str) -> str:
    return f"{_views_path(workspace_id)}/{view_id}"


async def _auth(client: AsyncClient, prefix: str) -> dict[str, str]:
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


async def _get_user_id(client: AsyncClient, headers: dict[str, str]) -> str:
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    return response_data(response)["id"]


async def _create_view(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: str,
    *,
    name: str = "My view",
    payload_extra: dict | None = None,
) -> dict:
    payload: dict[str, object] = {"name": name}
    if payload_extra:
        payload.update(payload_extra)
    response = await client.post(
        _views_path(workspace_id),
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201
    return response_data(response)


@pytest.mark.parametrize(
    "method",
    ["get", "post", "patch", "delete"],
)
async def test_case_list_view_unauthenticated_returns_401(
    client: AsyncClient,
    method: str,
) -> None:
    workspace_id = str(uuid.uuid4())
    view_id = str(uuid.uuid4())
    if method == "get":
        list_response = await client.get(_views_path(workspace_id))
        detail_response = await client.get(_view_detail_path(workspace_id, view_id))
        assert list_response.status_code == 401
        assert detail_response.status_code == 401
        return
    if method == "post":
        response = await client.post(
            _views_path(workspace_id),
            json={"name": "Guest view"},
        )
    elif method == "patch":
        response = await client.patch(
            _view_detail_path(workspace_id, view_id),
            json={"name": "Renamed"},
        )
    else:
        response = await client.delete(_view_detail_path(workspace_id, view_id))
    assert response.status_code == 401


@pytest.mark.parametrize(
    "method",
    ["get", "post", "patch", "delete"],
)
async def test_case_list_view_non_member_returns_404(
    client: AsyncClient,
    method: str,
) -> None:
    owner_headers = await _auth(client, "view-owner")
    workspace_id = await _create_workspace(client, owner_headers, "Private Views")
    created = await _create_view(client, owner_headers, workspace_id)
    view_id = created["id"]

    other_email = f"view-other-{uuid.uuid4()}@example.com"
    await register_user(client, email=other_email)
    other_headers = {
        "Authorization": f"Bearer {await login_user(client, email=other_email)}"
    }

    if method == "get":
        list_response = await client.get(
            _views_path(workspace_id),
            headers=other_headers,
        )
        detail_response = await client.get(
            _view_detail_path(workspace_id, view_id),
            headers=other_headers,
        )
        assert list_response.status_code == 404
        assert detail_response.status_code == 404
        return
    if method == "post":
        response = await client.post(
            _views_path(workspace_id),
            json={"name": "Forbidden view"},
            headers=other_headers,
        )
    elif method == "patch":
        response = await client.patch(
            _view_detail_path(workspace_id, view_id),
            json={"name": "Forbidden rename"},
            headers=other_headers,
        )
    else:
        response = await client.delete(
            _view_detail_path(workspace_id, view_id),
            headers=other_headers,
        )
    assert response.status_code == 404


async def test_workspace_member_can_create_saved_view(
    client: AsyncClient,
) -> None:
    headers = await _auth(client, "view-create")
    workspace_id = await _create_workspace(client, headers, "Create View Workspace")
    user_id = await _get_user_id(client, headers)

    data = await _create_view(
        client,
        headers,
        workspace_id,
        name="Open high priority",
        payload_extra={
            "description": "Open and urgent",
            "filters": {"status": "open", "priority": "high"},
            "sort_by": "priority",
            "sort_order": "desc",
            "page_size": 25,
            "is_default": True,
        },
    )

    assert data["name"] == "Open high priority"
    assert data["workspace_id"] == workspace_id
    assert data["created_by_user_id"] == user_id
    assert data["filters"] == {"status": "open", "priority": "high"}
    assert data["sort_by"] == "priority"
    assert data["sort_order"] == "desc"
    assert data["page_size"] == 25
    assert data["is_default"] is True


async def test_list_returns_only_workspace_views(client: AsyncClient) -> None:
    headers = await _auth(client, "view-list")
    workspace_a = await _create_workspace(client, headers, "Views A")
    workspace_b = await _create_workspace(client, headers, "Views B")
    view_a = await _create_view(client, headers, workspace_a, name="View A")
    await _create_view(client, headers, workspace_b, name="View B")

    response = await client.get(_views_path(workspace_a), headers=headers)
    assert response.status_code == 200
    items = response_data(response)
    assert len(items) == 1
    assert items[0]["id"] == view_a["id"]


async def test_detail_returns_workspace_view(client: AsyncClient) -> None:
    headers = await _auth(client, "view-detail")
    workspace_id = await _create_workspace(client, headers, "Detail View Workspace")
    created = await _create_view(client, headers, workspace_id, name="Detail view")

    response = await client.get(
        _view_detail_path(workspace_id, created["id"]),
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["id"] == created["id"]


async def test_cross_workspace_detail_returns_404(client: AsyncClient) -> None:
    headers = await _auth(client, "view-cross-detail")
    workspace_a = await _create_workspace(client, headers, "Cross Detail A")
    workspace_b = await _create_workspace(client, headers, "Cross Detail B")
    created = await _create_view(client, headers, workspace_a, name="Only in A")

    response = await client.get(
        _view_detail_path(workspace_b, created["id"]),
        headers=headers,
    )
    assert response.status_code == 404


async def test_cross_workspace_update_returns_404(client: AsyncClient) -> None:
    headers = await _auth(client, "view-cross-update")
    workspace_a = await _create_workspace(client, headers, "Cross Update A")
    workspace_b = await _create_workspace(client, headers, "Cross Update B")
    created = await _create_view(client, headers, workspace_a, name="Update in A")

    response = await client.patch(
        _view_detail_path(workspace_b, created["id"]),
        json={"name": "Blocked rename"},
        headers=headers,
    )
    assert response.status_code == 404


async def test_cross_workspace_delete_returns_404(client: AsyncClient) -> None:
    headers = await _auth(client, "view-cross-delete")
    workspace_a = await _create_workspace(client, headers, "Cross Delete A")
    workspace_b = await _create_workspace(client, headers, "Cross Delete B")
    created = await _create_view(client, headers, workspace_a, name="Delete in A")

    response = await client.delete(
        _view_detail_path(workspace_b, created["id"]),
        headers=headers,
    )
    assert response.status_code == 404


async def test_update_can_rename_view(client: AsyncClient) -> None:
    headers = await _auth(client, "view-rename")
    workspace_id = await _create_workspace(client, headers, "Rename View Workspace")
    created = await _create_view(client, headers, workspace_id, name="Old name")

    response = await client.patch(
        _view_detail_path(workspace_id, created["id"]),
        json={"name": "New name"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response)["name"] == "New name"


async def test_update_can_change_filters_sort_page_size_and_default(
    client: AsyncClient,
) -> None:
    headers = await _auth(client, "view-update-fields")
    workspace_id = await _create_workspace(client, headers, "Update Fields Workspace")
    created = await _create_view(client, headers, workspace_id, name="Mutable view")

    response = await client.patch(
        _view_detail_path(workspace_id, created["id"]),
        json={
            "filters": {"status": "pending"},
            "sort_by": "updated_at",
            "sort_order": "asc",
            "page_size": 100,
            "is_default": True,
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response_data(response)
    assert data["filters"] == {"status": "pending"}
    assert data["sort_by"] == "updated_at"
    assert data["sort_order"] == "asc"
    assert data["page_size"] == 100
    assert data["is_default"] is True


async def test_delete_removes_view(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await _auth(client, "view-delete")
    workspace_id = await _create_workspace(client, headers, "Delete View Workspace")
    created = await _create_view(client, headers, workspace_id, name="Delete me")
    view_id = created["id"]

    response = await client.delete(
        _view_detail_path(workspace_id, view_id),
        headers=headers,
    )
    assert response.status_code == 200
    assert response_data(response) == {"id": view_id, "deleted": True}

    view = await db_session.scalar(
        select(CaseListView).where(CaseListView.id == uuid.UUID(view_id)),
    )
    assert view is None


async def test_duplicate_name_in_same_workspace_is_blocked(
    client: AsyncClient,
) -> None:
    headers = await _auth(client, "view-dup-same")
    workspace_id = await _create_workspace(client, headers, "Duplicate Same Workspace")
    await _create_view(client, headers, workspace_id, name="Unique name")

    response = await client.post(
        _views_path(workspace_id),
        json={"name": "Unique name"},
        headers=headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Saved view name already exists in this workspace"
    )


async def test_duplicate_name_across_workspaces_is_allowed(
    client: AsyncClient,
) -> None:
    headers = await _auth(client, "view-dup-cross")
    workspace_a = await _create_workspace(client, headers, "Duplicate Cross A")
    workspace_b = await _create_workspace(client, headers, "Duplicate Cross B")
    view_a = await _create_view(client, headers, workspace_a, name="Shared view name")
    view_b = await _create_view(client, headers, workspace_b, name="Shared view name")

    assert view_a["id"] != view_b["id"]
    assert view_a["workspace_id"] != view_b["workspace_id"]


async def test_name_trimming_works(client: AsyncClient) -> None:
    headers = await _auth(client, "view-trim")
    workspace_id = await _create_workspace(client, headers, "Trim View Workspace")

    response = await client.post(
        _views_path(workspace_id),
        json={"name": "  Trimmed view  "},
        headers=headers,
    )
    assert response.status_code == 201
    assert response_data(response)["name"] == "Trimmed view"


async def test_empty_name_returns_422(client: AsyncClient) -> None:
    headers = await _auth(client, "view-empty-name")
    workspace_id = await _create_workspace(client, headers, "Empty Name Workspace")

    response = await client.post(
        _views_path(workspace_id),
        json={"name": "   "},
        headers=headers,
    )
    assert response.status_code == 422


async def test_invalid_sort_by_returns_422(client: AsyncClient) -> None:
    headers = await _auth(client, "view-bad-sort-by")
    workspace_id = await _create_workspace(client, headers, "Bad Sort By Workspace")

    response = await client.post(
        _views_path(workspace_id),
        json={"name": "Bad sort", "sort_by": "title"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_invalid_sort_order_returns_422(client: AsyncClient) -> None:
    headers = await _auth(client, "view-bad-sort-order")
    workspace_id = await _create_workspace(client, headers, "Bad Sort Order Workspace")

    response = await client.post(
        _views_path(workspace_id),
        json={"name": "Bad order", "sort_order": "sideways"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_invalid_page_size_returns_422(client: AsyncClient) -> None:
    headers = await _auth(client, "view-bad-page-size")
    workspace_id = await _create_workspace(client, headers, "Bad Page Size Workspace")

    response = await client.post(
        _views_path(workspace_id),
        json={"name": "Bad page", "page_size": 15},
        headers=headers,
    )
    assert response.status_code == 422


async def test_is_default_true_unsets_other_defaults_in_same_workspace(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await _auth(client, "view-default-same")
    workspace_id = await _create_workspace(client, headers, "Default Same Workspace")
    first = await _create_view(
        client,
        headers,
        workspace_id,
        name="First default",
        payload_extra={"is_default": True},
    )
    second = await _create_view(
        client,
        headers,
        workspace_id,
        name="Second default",
        payload_extra={"is_default": True},
    )

    first_view = await db_session.get(CaseListView, uuid.UUID(first["id"]))
    second_view = await db_session.get(CaseListView, uuid.UUID(second["id"]))
    assert first_view is not None
    assert second_view is not None
    assert first_view.is_default is False
    assert second_view.is_default is True


async def test_is_default_does_not_affect_other_workspaces(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await _auth(client, "view-default-cross")
    workspace_a = await _create_workspace(client, headers, "Default Cross A")
    workspace_b = await _create_workspace(client, headers, "Default Cross B")
    view_a = await _create_view(
        client,
        headers,
        workspace_a,
        name="Default A",
        payload_extra={"is_default": True},
    )
    view_b = await _create_view(
        client,
        headers,
        workspace_b,
        name="Default B",
        payload_extra={"is_default": True},
    )

    refreshed_a = await db_session.get(CaseListView, uuid.UUID(view_a["id"]))
    refreshed_b = await db_session.get(CaseListView, uuid.UUID(view_b["id"]))
    assert refreshed_a is not None
    assert refreshed_b is not None
    assert refreshed_a.is_default is True
    assert refreshed_b.is_default is True


async def test_deleting_default_view_does_not_promote_another(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await _auth(client, "view-delete-default")
    workspace_id = await _create_workspace(client, headers, "Delete Default Workspace")
    default_view = await _create_view(
        client,
        headers,
        workspace_id,
        name="Default to delete",
        payload_extra={"is_default": True},
    )
    other_view = await _create_view(
        client,
        headers,
        workspace_id,
        name="Other view",
    )

    response = await client.delete(
        _view_detail_path(workspace_id, default_view["id"]),
        headers=headers,
    )
    assert response.status_code == 200

    other = await db_session.get(CaseListView, uuid.UUID(other_view["id"]))
    assert other is not None
    assert other.is_default is False
