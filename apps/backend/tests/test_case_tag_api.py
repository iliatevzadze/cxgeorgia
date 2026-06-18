"""Tests for Universal Case tag API."""

import uuid
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_tag import CaseTag, UniversalCaseTag
from app.models.universal_case import UniversalCase
from tests.conftest import auth_headers, response_data

pytestmark = pytest.mark.asyncio


def _workspace_tags_path(workspace_id: str) -> str:
    return f"/api/v1/workspaces/{workspace_id}/case-tags"


def _workspace_tag_detail_path(workspace_id: str, tag_id: str) -> str:
    return f"{_workspace_tags_path(workspace_id)}/{tag_id}"


def _case_tags_path(workspace_id: str, case_id: str) -> str:
    return f"/api/v1/workspaces/{workspace_id}/cases/{case_id}/tags"


def _case_tag_detail_path(workspace_id: str, case_id: str, tag_id: str) -> str:
    return f"{_case_tags_path(workspace_id, case_id)}/{tag_id}"


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
    title: str = "Tag test case",
) -> str:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": title},
        headers=headers,
    )
    assert response.status_code == 201
    return response_data(response)["id"]


async def _create_tag(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: str,
    *,
    name: str = "Urgent",
    slug: str = "urgent",
    color: str | None = "#ff0000",
) -> dict:
    payload: dict[str, object] = {"name": name, "slug": slug}
    if color is not None:
        payload["color"] = color
    response = await client.post(
        _workspace_tags_path(workspace_id),
        json=payload,
        headers=headers,
    )
    return response


async def test_create_workspace_tag_as_member(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"tag-create-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Tag Create Workspace")

    response = await _create_tag(client, headers, workspace_id)
    assert response.status_code == 201
    data = response_data(response)
    assert data["workspace_id"] == workspace_id
    assert data["name"] == "Urgent"
    assert data["slug"] == "urgent"
    assert data["color"] == "#ff0000"
    assert data["id"]
    assert data["created_at"]
    assert data["updated_at"]


async def test_create_workspace_tag_unauthenticated_returns_401(
    client: AsyncClient,
) -> None:
    response = await client.post(
        _workspace_tags_path(str(uuid.uuid4())),
        json={"name": "Urgent", "slug": "urgent"},
    )
    assert response.status_code == 401


async def test_create_workspace_tag_non_member_returns_404(
    client: AsyncClient,
) -> None:
    owner_headers = await auth_headers(
        client,
        f"tag-owner-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, owner_headers, "Tag Owner Workspace")

    outsider_headers = await auth_headers(
        client,
        f"tag-outsider-{uuid.uuid4()}@example.com",
    )
    response = await _create_tag(client, outsider_headers, workspace_id)
    assert response.status_code == 404


async def test_list_workspace_tags_returns_only_workspace_tags(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"tag-list-{uuid.uuid4()}@example.com")
    workspace_a = await _create_workspace(client, headers, "Tag List Workspace A")
    workspace_b = await _create_workspace(client, headers, "Tag List Workspace B")

    create_a = await _create_tag(
        client,
        headers,
        workspace_a,
        name="Billing",
        slug="billing",
    )
    assert create_a.status_code == 201
    create_b = await _create_tag(
        client,
        headers,
        workspace_b,
        name="Other",
        slug="other",
    )
    assert create_b.status_code == 201

    response = await client.get(_workspace_tags_path(workspace_a), headers=headers)
    assert response.status_code == 200
    items = response_data(response)
    assert len(items) == 1
    assert items[0]["slug"] == "billing"
    assert items[0]["workspace_id"] == workspace_a


async def test_list_workspace_tags_non_member_returns_404(
    client: AsyncClient,
) -> None:
    owner_headers = await auth_headers(
        client,
        f"tag-list-owner-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, owner_headers, "Tag List Owner")

    outsider_headers = await auth_headers(
        client,
        f"tag-list-outsider-{uuid.uuid4()}@example.com",
    )
    response = await client.get(
        _workspace_tags_path(workspace_id),
        headers=outsider_headers,
    )
    assert response.status_code == 404


async def test_same_slug_in_same_workspace_returns_422(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"tag-dup-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Tag Dup Workspace")

    first = await _create_tag(
        client,
        headers,
        workspace_id,
        name="Billing",
        slug="billing",
    )
    assert first.status_code == 201

    second = await _create_tag(
        client,
        headers,
        workspace_id,
        name="Billing duplicate",
        slug="billing",
    )
    assert second.status_code == 422


async def test_same_slug_in_different_workspaces_is_allowed(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"tag-cross-{uuid.uuid4()}@example.com")
    workspace_a = await _create_workspace(client, headers, "Tag Cross A")
    workspace_b = await _create_workspace(client, headers, "Tag Cross B")

    first = await _create_tag(
        client,
        headers,
        workspace_a,
        name="Shared",
        slug="shared-slug",
    )
    second = await _create_tag(
        client,
        headers,
        workspace_b,
        name="Shared",
        slug="shared-slug",
    )
    assert first.status_code == 201
    assert second.status_code == 201


async def test_update_workspace_tag_name_color_slug(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"tag-update-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Tag Update Workspace")
    create_response = await _create_tag(
        client,
        headers,
        workspace_id,
        name="Original",
        slug="original",
        color="#111111",
    )
    tag_id = response_data(create_response)["id"]

    response = await client.patch(
        _workspace_tag_detail_path(workspace_id, tag_id),
        json={"name": "Updated", "slug": "updated", "color": "#222222"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response_data(response)
    assert data["name"] == "Updated"
    assert data["slug"] == "updated"
    assert data["color"] == "#222222"


async def test_update_workspace_tag_duplicate_slug_returns_422(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"tag-update-dup-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Tag Update Dup Workspace")
    first = await _create_tag(
        client,
        headers,
        workspace_id,
        name="First",
        slug="first",
    )
    second = await _create_tag(
        client,
        headers,
        workspace_id,
        name="Second",
        slug="second",
    )
    tag_id = response_data(second)["id"]
    assert first.status_code == 201
    assert second.status_code == 201

    response = await client.patch(
        _workspace_tag_detail_path(workspace_id, tag_id),
        json={"slug": "first"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_update_workspace_tag_non_member_returns_404(
    client: AsyncClient,
) -> None:
    owner_headers = await auth_headers(
        client,
        f"tag-update-owner-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, owner_headers, "Tag Update Owner")
    create_response = await _create_tag(
        client,
        owner_headers,
        workspace_id,
        name="Protected",
        slug="protected",
    )
    tag_id = response_data(create_response)["id"]

    outsider_headers = await auth_headers(
        client,
        f"tag-update-outsider-{uuid.uuid4()}@example.com",
    )
    response = await client.patch(
        _workspace_tag_detail_path(workspace_id, tag_id),
        json={"name": "Hacked"},
        headers=outsider_headers,
    )
    assert response.status_code == 404


async def test_delete_workspace_tag_removes_tag(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"tag-delete-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Tag Delete Workspace")
    create_response = await _create_tag(
        client,
        headers,
        workspace_id,
        name="Temporary",
        slug="temporary",
    )
    tag_id = response_data(create_response)["id"]

    delete_response = await client.delete(
        _workspace_tag_detail_path(workspace_id, tag_id),
        headers=headers,
    )
    assert delete_response.status_code == 200
    assert response_data(delete_response)["deleted"] is True

    list_response = await client.get(
        _workspace_tags_path(workspace_id),
        headers=headers,
    )
    assert response_data(list_response) == []


async def test_delete_workspace_tag_does_not_delete_case(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"tag-delete-case-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Tag Delete Case Workspace")
    case_id = await _create_case(client, headers, workspace_id)
    create_response = await _create_tag(
        client,
        headers,
        workspace_id,
        name="Case tag",
        slug="case-tag",
    )
    tag_id = response_data(create_response)["id"]

    attach_response = await client.post(
        _case_tag_detail_path(workspace_id, case_id, tag_id),
        headers=headers,
    )
    assert attach_response.status_code == 201

    delete_response = await client.delete(
        _workspace_tag_detail_path(workspace_id, tag_id),
        headers=headers,
    )
    assert delete_response.status_code == 200

    case = await db_session.get(UniversalCase, UUID(case_id))
    assert case is not None


async def test_delete_workspace_tag_non_member_returns_404(
    client: AsyncClient,
) -> None:
    owner_headers = await auth_headers(
        client,
        f"tag-delete-owner-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, owner_headers, "Tag Delete Owner")
    create_response = await _create_tag(
        client,
        owner_headers,
        workspace_id,
        name="Protected",
        slug="protected-delete",
    )
    tag_id = response_data(create_response)["id"]

    outsider_headers = await auth_headers(
        client,
        f"tag-delete-outsider-{uuid.uuid4()}@example.com",
    )
    response = await client.delete(
        _workspace_tag_detail_path(workspace_id, tag_id),
        headers=outsider_headers,
    )
    assert response.status_code == 404


async def test_attach_tag_to_case_as_member(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"tag-attach-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Tag Attach Workspace")
    case_id = await _create_case(client, headers, workspace_id)
    create_response = await _create_tag(
        client,
        headers,
        workspace_id,
        name="VIP",
        slug="vip",
    )
    tag_id = response_data(create_response)["id"]

    response = await client.post(
        _case_tag_detail_path(workspace_id, case_id, tag_id),
        headers=headers,
    )
    assert response.status_code == 201
    data = response_data(response)
    assert data["id"] == tag_id
    assert data["slug"] == "vip"


async def test_list_case_tags_returns_attached_tags(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"tag-case-list-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Tag Case List Workspace")
    case_id = await _create_case(client, headers, workspace_id)
    first = await _create_tag(
        client,
        headers,
        workspace_id,
        name="Alpha",
        slug="alpha",
    )
    second = await _create_tag(
        client,
        headers,
        workspace_id,
        name="Beta",
        slug="beta",
    )
    tag_a = response_data(first)["id"]
    tag_b = response_data(second)["id"]

    assert (
        await client.post(
            _case_tag_detail_path(workspace_id, case_id, tag_a),
            headers=headers,
        )
    ).status_code == 201
    assert (
        await client.post(
            _case_tag_detail_path(workspace_id, case_id, tag_b),
            headers=headers,
        )
    ).status_code == 201

    response = await client.get(
        _case_tags_path(workspace_id, case_id),
        headers=headers,
    )
    assert response.status_code == 200
    slugs = {item["slug"] for item in response_data(response)}
    assert slugs == {"alpha", "beta"}


async def test_attach_same_tag_twice_is_idempotent(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"tag-idempotent-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Tag Idempotent Workspace")
    case_id = await _create_case(client, headers, workspace_id)
    create_response = await _create_tag(
        client,
        headers,
        workspace_id,
        name="Repeat",
        slug="repeat",
    )
    tag_id = response_data(create_response)["id"]

    first = await client.post(
        _case_tag_detail_path(workspace_id, case_id, tag_id),
        headers=headers,
    )
    second = await client.post(
        _case_tag_detail_path(workspace_id, case_id, tag_id),
        headers=headers,
    )
    assert first.status_code == 201
    assert second.status_code == 200
    assert response_data(second)["id"] == tag_id


async def test_detach_tag_from_case(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"tag-detach-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Tag Detach Workspace")
    case_id = await _create_case(client, headers, workspace_id)
    create_response = await _create_tag(
        client,
        headers,
        workspace_id,
        name="Detach me",
        slug="detach-me",
    )
    tag_id = response_data(create_response)["id"]

    attach_response = await client.post(
        _case_tag_detail_path(workspace_id, case_id, tag_id),
        headers=headers,
    )
    assert attach_response.status_code == 201

    detach_response = await client.delete(
        _case_tag_detail_path(workspace_id, case_id, tag_id),
        headers=headers,
    )
    assert detach_response.status_code == 200
    assert response_data(detach_response)["detached"] is True

    list_response = await client.get(
        _case_tags_path(workspace_id, case_id),
        headers=headers,
    )
    assert response_data(list_response) == []


async def test_detach_removes_join_row_but_not_tag_or_case(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"tag-detach-keep-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Tag Detach Keep Workspace")
    case_id = await _create_case(client, headers, workspace_id)
    create_response = await _create_tag(
        client,
        headers,
        workspace_id,
        name="Keep",
        slug="keep",
    )
    tag_id = response_data(create_response)["id"]

    await client.post(
        _case_tag_detail_path(workspace_id, case_id, tag_id),
        headers=headers,
    )
    await client.delete(
        _case_tag_detail_path(workspace_id, case_id, tag_id),
        headers=headers,
    )

    assert await db_session.get(CaseTag, UUID(tag_id)) is not None
    assert await db_session.get(UniversalCase, UUID(case_id)) is not None
    join_rows = (
        await db_session.scalars(
            select(UniversalCaseTag).where(UniversalCaseTag.case_id == UUID(case_id))
        )
    ).all()
    assert join_rows == []


async def test_detach_not_attached_returns_404(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"tag-detach-missing-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Tag Detach Missing Workspace",
    )
    case_id = await _create_case(client, headers, workspace_id)
    create_response = await _create_tag(
        client,
        headers,
        workspace_id,
        name="Unattached",
        slug="unattached",
    )
    tag_id = response_data(create_response)["id"]

    response = await client.delete(
        _case_tag_detail_path(workspace_id, case_id, tag_id),
        headers=headers,
    )
    assert response.status_code == 404


async def test_cannot_attach_tag_from_another_workspace(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"tag-cross-attach-{uuid.uuid4()}@example.com")
    workspace_a = await _create_workspace(client, headers, "Tag Cross Attach A")
    workspace_b = await _create_workspace(client, headers, "Tag Cross Attach B")
    case_id = await _create_case(client, headers, workspace_a)
    foreign_tag = await _create_tag(
        client,
        headers,
        workspace_b,
        name="Foreign",
        slug="foreign",
    )
    tag_id = response_data(foreign_tag)["id"]

    response = await client.post(
        _case_tag_detail_path(workspace_a, case_id, tag_id),
        headers=headers,
    )
    assert response.status_code == 404


async def test_cannot_attach_tag_to_case_from_another_workspace(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"tag-cross-case-{uuid.uuid4()}@example.com",
    )
    workspace_a = await _create_workspace(client, headers, "Tag Cross Case A")
    workspace_b = await _create_workspace(client, headers, "Tag Cross Case B")
    case_id = await _create_case(client, headers, workspace_b)
    tag_response = await _create_tag(
        client,
        headers,
        workspace_a,
        name="Local",
        slug="local",
    )
    tag_id = response_data(tag_response)["id"]

    response = await client.post(
        _case_tag_detail_path(workspace_a, case_id, tag_id),
        headers=headers,
    )
    assert response.status_code == 404


async def test_case_tag_attachment_non_member_returns_404(
    client: AsyncClient,
) -> None:
    owner_headers = await auth_headers(
        client,
        f"tag-attach-owner-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, owner_headers, "Tag Attach Owner")
    case_id = await _create_case(client, owner_headers, workspace_id)
    create_response = await _create_tag(
        client,
        owner_headers,
        workspace_id,
        name="Member only",
        slug="member-only",
    )
    tag_id = response_data(create_response)["id"]

    outsider_headers = await auth_headers(
        client,
        f"tag-attach-outsider-{uuid.uuid4()}@example.com",
    )
    attach_response = await client.post(
        _case_tag_detail_path(workspace_id, case_id, tag_id),
        headers=outsider_headers,
    )
    list_response = await client.get(
        _case_tags_path(workspace_id, case_id),
        headers=outsider_headers,
    )
    detach_response = await client.delete(
        _case_tag_detail_path(workspace_id, case_id, tag_id),
        headers=outsider_headers,
    )
    assert attach_response.status_code == 404
    assert list_response.status_code == 404
    assert detach_response.status_code == 404


async def test_deleting_case_removes_join_rows_but_leaves_tag(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"tag-delete-case-join-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Tag Delete Case Join")
    case_id = await _create_case(client, headers, workspace_id)
    create_response = await _create_tag(
        client,
        headers,
        workspace_id,
        name="Survivor",
        slug="survivor",
    )
    tag_id = response_data(create_response)["id"]

    await client.post(
        _case_tag_detail_path(workspace_id, case_id, tag_id),
        headers=headers,
    )

    delete_case_response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        headers=headers,
    )
    assert delete_case_response.status_code == 200

    assert await db_session.get(CaseTag, UUID(tag_id)) is not None
    join_rows = (
        await db_session.scalars(
            select(UniversalCaseTag).where(UniversalCaseTag.tag_id == UUID(tag_id))
        )
    ).all()
    assert join_rows == []


async def test_deleting_tag_removes_join_rows_but_leaves_case(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"tag-delete-tag-join-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Tag Delete Tag Join")
    case_id = await _create_case(client, headers, workspace_id)
    create_response = await _create_tag(
        client,
        headers,
        workspace_id,
        name="Disposable",
        slug="disposable",
    )
    tag_id = response_data(create_response)["id"]

    await client.post(
        _case_tag_detail_path(workspace_id, case_id, tag_id),
        headers=headers,
    )

    delete_tag_response = await client.delete(
        _workspace_tag_detail_path(workspace_id, tag_id),
        headers=headers,
    )
    assert delete_tag_response.status_code == 200

    assert await db_session.get(UniversalCase, UUID(case_id)) is not None
    join_rows = (
        await db_session.scalars(
            select(UniversalCaseTag).where(UniversalCaseTag.case_id == UUID(case_id))
        )
    ).all()
    assert join_rows == []
