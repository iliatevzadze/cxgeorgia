"""Tests for workspace bootstrap API."""

import uuid
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.slugify import slugify_workspace_name
from app.models.enums import WorkspaceMemberRole, WorkspaceMemberStatus, WorkspaceStatus
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_membership import WorkspaceMembership
from tests.conftest import auth_headers, login_user, register_user, response_data

pytestmark = pytest.mark.asyncio


async def test_create_workspace_as_authenticated_user(client: AsyncClient) -> None:
    workspace_name = f"Acme Support {uuid.uuid4().hex[:8]}"
    expected_slug = slugify_workspace_name(workspace_name)
    headers = await auth_headers(client, f"ws-create-{uuid.uuid4()}@example.com")
    response = await client.post(
        "/api/v1/workspaces",
        json={"name": workspace_name},
        headers=headers,
    )
    assert response.status_code == 201
    data = response_data(response)
    assert data["workspace"]["name"] == workspace_name
    assert data["workspace"]["slug"] == expected_slug
    assert data["workspace"]["status"] == "active"
    assert data["membership"]["role"] == "owner"
    assert data["membership"]["status"] == "active"


async def test_create_workspace_assigns_owner_membership(
    client: AsyncClient,
) -> None:
    email = f"ws-owner-{uuid.uuid4()}@example.com"
    headers = await auth_headers(client, email)
    response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Owner Workspace"},
        headers=headers,
    )
    membership = response_data(response)["membership"]
    me_response = await client.get("/api/v1/auth/me", headers=headers)
    user_id = response_data(me_response)["id"]
    assert membership["user_id"] == user_id
    assert membership["role"] == WorkspaceMemberRole.OWNER.value


async def test_create_workspace_unauthenticated_returns_401(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/workspaces",
        json={"name": "No Auth"},
    )
    assert response.status_code == 401


async def test_create_workspace_invalid_name_returns_422(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"ws-invalid-{uuid.uuid4()}@example.com")
    response = await client.post(
        "/api/v1/workspaces",
        json={"name": "A"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_create_workspace_duplicate_names_get_unique_slugs(
    client: AsyncClient,
) -> None:
    workspace_name = f"Duplicate Workspace {uuid.uuid4().hex[:8]}"
    base_slug = slugify_workspace_name(workspace_name)
    headers = await auth_headers(client, f"ws-dup-{uuid.uuid4()}@example.com")
    first = await client.post(
        "/api/v1/workspaces",
        json={"name": workspace_name},
        headers=headers,
    )
    second = await client.post(
        "/api/v1/workspaces",
        json={"name": workspace_name},
        headers=headers,
    )
    assert response_data(first)["workspace"]["slug"] == base_slug
    assert response_data(second)["workspace"]["slug"] == f"{base_slug}-2"


async def test_list_workspaces_returns_own_active_workspaces(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"ws-list-{uuid.uuid4()}@example.com")
    create_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Listed Workspace"},
        headers=headers,
    )
    workspace_id = response_data(create_response)["workspace"]["id"]

    list_response = await client.get("/api/v1/workspaces", headers=headers)
    assert list_response.status_code == 200
    items = response_data(list_response)
    assert len(items) == 1
    assert items[0]["workspace"]["id"] == workspace_id
    assert items[0]["membership"]["role"] == "owner"


async def test_list_workspaces_excludes_non_member_workspaces(
    client: AsyncClient,
) -> None:
    owner_email = f"ws-owner-only-{uuid.uuid4()}@example.com"
    other_email = f"ws-other-{uuid.uuid4()}@example.com"
    owner_headers = await auth_headers(client, owner_email)
    await client.post(
        "/api/v1/workspaces",
        json={"name": "Private Workspace"},
        headers=owner_headers,
    )

    await register_user(client, email=other_email)
    other_token = await login_user(client, email=other_email)
    other_headers = {"Authorization": f"Bearer {other_token}"}
    list_response = await client.get("/api/v1/workspaces", headers=other_headers)
    assert response_data(list_response) == []


async def test_list_workspaces_excludes_removed_membership(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    email = f"ws-removed-{uuid.uuid4()}@example.com"
    headers = await auth_headers(client, email)
    create_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Removed Membership"},
        headers=headers,
    )
    membership_id = response_data(create_response)["membership"]["id"]
    membership = await db_session.get(WorkspaceMembership, UUID(membership_id))
    assert membership is not None
    membership.status = WorkspaceMemberStatus.REMOVED
    await db_session.flush()

    list_response = await client.get("/api/v1/workspaces", headers=headers)
    assert response_data(list_response) == []


async def test_get_workspace_detail_for_active_member(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"ws-detail-{uuid.uuid4()}@example.com")
    create_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Detail Workspace"},
        headers=headers,
    )
    workspace_id = response_data(create_response)["workspace"]["id"]

    detail_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}",
        headers=headers,
    )
    assert detail_response.status_code == 200
    assert response_data(detail_response)["name"] == "Detail Workspace"


async def test_get_workspace_detail_non_member_returns_404(
    client: AsyncClient,
) -> None:
    owner_email = f"ws-owner-detail-{uuid.uuid4()}@example.com"
    owner_headers = await auth_headers(client, owner_email)
    create_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Hidden Workspace"},
        headers=owner_headers,
    )
    workspace_id = response_data(create_response)["workspace"]["id"]

    other_email = f"ws-nonmember-{uuid.uuid4()}@example.com"
    await register_user(client, email=other_email)
    other_headers = {
        "Authorization": f"Bearer {await login_user(client, email=other_email)}"
    }
    detail_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}",
        headers=other_headers,
    )
    assert detail_response.status_code == 404


async def test_get_workspace_detail_unknown_workspace_returns_404(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"ws-unknown-{uuid.uuid4()}@example.com")
    response = await client.get(
        f"/api/v1/workspaces/{uuid.uuid4()}",
        headers=headers,
    )
    assert response.status_code == 404


async def test_list_workspace_memberships_for_active_member(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"ws-members-{uuid.uuid4()}@example.com")
    create_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Members Workspace"},
        headers=headers,
    )
    workspace_id = response_data(create_response)["workspace"]["id"]

    memberships_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/memberships",
        headers=headers,
    )
    assert memberships_response.status_code == 200
    memberships = response_data(memberships_response)
    assert len(memberships) == 1
    assert memberships[0]["role"] == "owner"
    assert memberships[0]["status"] == "active"


async def test_list_workspace_memberships_non_member_returns_404(
    client: AsyncClient,
) -> None:
    owner_headers = await auth_headers(
        client,
        f"ws-owner-members-{uuid.uuid4()}@example.com",
    )
    create_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Members Hidden"},
        headers=owner_headers,
    )
    workspace_id = response_data(create_response)["workspace"]["id"]

    other_email = f"ws-members-nonmember-{uuid.uuid4()}@example.com"
    await register_user(client, email=other_email)
    other_headers = {
        "Authorization": f"Bearer {await login_user(client, email=other_email)}"
    }
    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/memberships",
        headers=other_headers,
    )
    assert response.status_code == 404


async def test_list_workspace_memberships_unauthenticated_returns_401(
    client: AsyncClient,
) -> None:
    response = await client.get(f"/api/v1/workspaces/{uuid.uuid4()}/memberships")
    assert response.status_code == 401


async def test_create_workspace_persists_active_workspace_and_owner(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    email = f"ws-persist-{uuid.uuid4()}@example.com"
    headers = await auth_headers(client, email)
    response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Persisted Workspace"},
        headers=headers,
    )
    workspace_id = UUID(response_data(response)["workspace"]["id"])
    workspace = await db_session.get(Workspace, workspace_id)
    assert workspace is not None
    assert workspace.status == WorkspaceStatus.ACTIVE

    user = await db_session.scalar(select(User).where(User.email == email))
    assert user is not None
    membership = await db_session.scalar(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user.id,
        )
    )
    assert membership is not None
    assert membership.role == WorkspaceMemberRole.OWNER
