"""Tests for Universal Case comment API."""

import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_comment import CaseComment
from app.models.enums import CaseStatus
from app.models.universal_case import UniversalCase
from tests.conftest import auth_headers, login_user, register_user, response_data

pytestmark = pytest.mark.asyncio


def _comments_path(workspace_id: str, case_id: str) -> str:
    return f"/api/v1/workspaces/{workspace_id}/cases/{case_id}/comments"


def _comment_detail_path(
    workspace_id: str,
    case_id: str,
    comment_id: str,
) -> str:
    return f"{_comments_path(workspace_id, case_id)}/{comment_id}"


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
    title: str = "Comment test case",
) -> str:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": title},
        headers=headers,
    )
    assert response.status_code == 201
    return response_data(response)["id"]


async def _create_comment(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: str,
    case_id: str,
    *,
    body: str = "Test comment",
    is_internal: bool | None = None,
) -> dict:
    payload: dict[str, object] = {"body": body}
    if is_internal is not None:
        payload["is_internal"] = is_internal
    response = await client.post(
        _comments_path(workspace_id, case_id),
        json=payload,
        headers=headers,
    )
    return response


async def test_create_comment_unauthenticated_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        _comments_path(str(uuid.uuid4()), str(uuid.uuid4())),
        json={"body": "Unauthorized comment"},
    )
    assert response.status_code == 401


async def test_list_comments_unauthenticated_returns_401(client: AsyncClient) -> None:
    response = await client.get(
        _comments_path(str(uuid.uuid4()), str(uuid.uuid4())),
    )
    assert response.status_code == 401


async def test_create_comment_as_workspace_member(client: AsyncClient) -> None:
    email = f"comment-create-{uuid.uuid4()}@example.com"
    headers = await auth_headers(client, email)
    workspace_id = await _create_workspace(client, headers, "Comment Create Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    me_response = await client.get("/api/v1/auth/me", headers=headers)
    user_id = response_data(me_response)["id"]

    response = await _create_comment(client, headers, workspace_id, case_id)
    assert response.status_code == 201
    data = response_data(response)
    assert data["workspace_id"] == workspace_id
    assert data["case_id"] == case_id
    assert data["author_user_id"] == user_id
    assert data["body"] == "Test comment"
    assert data["is_internal"] is True
    assert data["id"]
    assert data["created_at"]
    assert data["updated_at"]


async def test_create_comment_response_uses_envelope(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"comment-envelope-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Comment Envelope Workspace",
    )
    case_id = await _create_case(client, headers, workspace_id)

    response = await _create_comment(
        client,
        headers,
        workspace_id,
        case_id,
        body="Envelope comment",
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["error"] is None
    assert payload["meta"] == {}
    assert payload["data"]["body"] == "Envelope comment"


async def test_create_comment_trims_body(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"comment-trim-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Comment Trim Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    response = await _create_comment(
        client,
        headers,
        workspace_id,
        case_id,
        body="  Trimmed comment  ",
    )
    assert response.status_code == 201
    assert response_data(response)["body"] == "Trimmed comment"


async def test_create_comment_whitespace_only_body_returns_422(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"comment-blank-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Comment Blank Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    response = await _create_comment(
        client,
        headers,
        workspace_id,
        case_id,
        body="   ",
    )
    assert response.status_code == 422


async def test_create_comment_missing_body_returns_422(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"comment-missing-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Comment Missing Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.post(
        _comments_path(workspace_id, case_id),
        json={},
        headers=headers,
    )
    assert response.status_code == 422


async def test_create_comment_extra_field_returns_422(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"comment-extra-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Comment Extra Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.post(
        _comments_path(workspace_id, case_id),
        json={"body": "Valid comment", "unexpected": "field"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_create_comment_is_internal_defaults_to_true(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"comment-internal-default-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Comment Internal Default Workspace",
    )
    case_id = await _create_case(client, headers, workspace_id)

    response = await _create_comment(
        client,
        headers,
        workspace_id,
        case_id,
        body="Default internal comment",
    )
    assert response.status_code == 201
    assert response_data(response)["is_internal"] is True


async def test_create_comment_is_internal_false_is_accepted(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"comment-external-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Comment External Workspace",
    )
    case_id = await _create_case(client, headers, workspace_id)

    response = await _create_comment(
        client,
        headers,
        workspace_id,
        case_id,
        body="External comment",
        is_internal=False,
    )
    assert response.status_code == 201
    assert response_data(response)["is_internal"] is False


async def test_create_comment_is_internal_null_returns_422(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"comment-null-internal-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Comment Null Internal Workspace",
    )
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.post(
        _comments_path(workspace_id, case_id),
        json={"body": "Comment", "is_internal": None},
        headers=headers,
    )
    assert response.status_code == 422


async def test_list_comments_returns_oldest_first(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(client, f"comment-order-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Comment Order Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    first_response = await _create_comment(
        client,
        headers,
        workspace_id,
        case_id,
        body="First comment",
    )
    second_response = await _create_comment(
        client,
        headers,
        workspace_id,
        case_id,
        body="Second comment",
    )
    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_id = response_data(first_response)["id"]
    second_id = response_data(second_response)["id"]
    first_comment = await db_session.get(CaseComment, UUID(first_id))
    second_comment = await db_session.get(CaseComment, UUID(second_id))
    assert first_comment is not None
    assert second_comment is not None
    first_comment.created_at = datetime.now(UTC) - timedelta(hours=1)
    second_comment.created_at = datetime.now(UTC)
    await db_session.flush()

    list_response = await client.get(
        _comments_path(workspace_id, case_id),
        headers=headers,
    )
    assert list_response.status_code == 200
    items = response_data(list_response)
    assert [item["id"] for item in items] == [first_id, second_id]
    assert [item["body"] for item in items] == ["First comment", "Second comment"]


async def test_list_comments_excludes_other_case_in_same_workspace(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"comment-case-iso-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Comment Case Iso Workspace",
    )
    case_a = await _create_case(client, headers, workspace_id, title="Case A")
    case_b = await _create_case(client, headers, workspace_id, title="Case B")

    await _create_comment(
        client,
        headers,
        workspace_id,
        case_a,
        body="Comment on case A",
    )
    await _create_comment(
        client,
        headers,
        workspace_id,
        case_b,
        body="Comment on case B",
    )

    list_response = await client.get(
        _comments_path(workspace_id, case_a),
        headers=headers,
    )
    assert list_response.status_code == 200
    items = response_data(list_response)
    assert len(items) == 1
    assert items[0]["case_id"] == case_a
    assert items[0]["body"] == "Comment on case A"


async def test_list_comments_excludes_other_workspace(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"comment-workspace-iso-{uuid.uuid4()}@example.com",
    )
    workspace_a = await _create_workspace(client, headers, "Comment Workspace A")
    workspace_b = await _create_workspace(client, headers, "Comment Workspace B")
    case_a = await _create_case(client, headers, workspace_a, title="Case in A")

    await _create_comment(
        client,
        headers,
        workspace_a,
        case_a,
        body="Comment in workspace A",
    )

    other_case = UniversalCase(
        workspace_id=UUID(workspace_b),
        title="Case in B",
        status=CaseStatus.OPEN,
    )
    db_session.add(other_case)
    await db_session.flush()
    db_session.add(
        CaseComment(
            workspace_id=UUID(workspace_b),
            case_id=other_case.id,
            body="Comment in workspace B",
        )
    )
    await db_session.flush()

    list_response = await client.get(
        _comments_path(workspace_a, case_a),
        headers=headers,
    )
    assert list_response.status_code == 200
    items = response_data(list_response)
    assert len(items) == 1
    assert items[0]["workspace_id"] == workspace_a
    assert items[0]["body"] == "Comment in workspace A"


async def test_create_comment_cross_workspace_returns_404(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"comment-cross-post-{uuid.uuid4()}@example.com",
    )
    workspace_a = await _create_workspace(client, headers, "Comment Cross A")
    workspace_b = await _create_workspace(client, headers, "Comment Cross B")
    case_id = await _create_case(client, headers, workspace_a)

    response = await _create_comment(client, headers, workspace_b, case_id)
    assert response.status_code == 404


async def test_list_comments_cross_workspace_returns_404(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"comment-cross-get-{uuid.uuid4()}@example.com",
    )
    workspace_a = await _create_workspace(client, headers, "Comment Cross Get A")
    workspace_b = await _create_workspace(client, headers, "Comment Cross Get B")
    case_id = await _create_case(client, headers, workspace_a)

    response = await client.get(
        _comments_path(workspace_b, case_id),
        headers=headers,
    )
    assert response.status_code == 404


async def test_create_comment_non_member_returns_404(client: AsyncClient) -> None:
    owner_email = f"comment-owner-{uuid.uuid4()}@example.com"
    other_email = f"comment-other-{uuid.uuid4()}@example.com"
    owner_headers = await auth_headers(client, owner_email)
    workspace_id = await _create_workspace(client, owner_headers, "Comment Private")
    case_id = await _create_case(client, owner_headers, workspace_id)

    await register_user(client, email=other_email)
    other_headers = {
        "Authorization": f"Bearer {await login_user(client, email=other_email)}"
    }
    response = await _create_comment(client, other_headers, workspace_id, case_id)
    assert response.status_code == 404


async def test_list_comments_non_member_returns_404(client: AsyncClient) -> None:
    owner_email = f"comment-owner-list-{uuid.uuid4()}@example.com"
    other_email = f"comment-other-list-{uuid.uuid4()}@example.com"
    owner_headers = await auth_headers(client, owner_email)
    workspace_id = await _create_workspace(
        client,
        owner_headers,
        "Comment Private List",
    )
    case_id = await _create_case(client, owner_headers, workspace_id)

    await register_user(client, email=other_email)
    other_headers = {
        "Authorization": f"Bearer {await login_user(client, email=other_email)}"
    }
    response = await client.get(
        _comments_path(workspace_id, case_id),
        headers=other_headers,
    )
    assert response.status_code == 404


async def test_delete_comment_unauthenticated_returns_401(client: AsyncClient) -> None:
    response = await client.delete(
        _comment_detail_path(
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            str(uuid.uuid4()),
        ),
    )
    assert response.status_code == 401


async def test_delete_comment_as_workspace_member(client: AsyncClient) -> None:
    headers = await auth_headers(client, f"comment-delete-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Comment Delete Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    create_response = await _create_comment(
        client,
        headers,
        workspace_id,
        case_id,
        body="Delete me",
    )
    assert create_response.status_code == 201
    comment_id = response_data(create_response)["id"]

    delete_response = await client.delete(
        _comment_detail_path(workspace_id, case_id, comment_id),
        headers=headers,
    )
    assert delete_response.status_code == 200
    data = response_data(delete_response)
    assert data["id"] == comment_id
    assert data["deleted"] is True


async def test_delete_comment_response_uses_envelope(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"comment-delete-envelope-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Comment Delete Envelope",
    )
    case_id = await _create_case(client, headers, workspace_id)
    create_response = await _create_comment(client, headers, workspace_id, case_id)
    comment_id = response_data(create_response)["id"]

    delete_response = await client.delete(
        _comment_detail_path(workspace_id, case_id, comment_id),
        headers=headers,
    )
    assert delete_response.status_code == 200
    payload = delete_response.json()
    assert payload["error"] is None
    assert payload["meta"] == {}
    assert payload["data"]["deleted"] is True


async def test_delete_comment_removed_from_list(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"comment-delete-list-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Comment Delete List")
    case_id = await _create_case(client, headers, workspace_id)

    keep_response = await _create_comment(
        client,
        headers,
        workspace_id,
        case_id,
        body="Keep this comment",
    )
    delete_response = await _create_comment(
        client,
        headers,
        workspace_id,
        case_id,
        body="Remove this comment",
    )
    assert keep_response.status_code == 201
    assert delete_response.status_code == 201
    keep_id = response_data(keep_response)["id"]
    remove_id = response_data(delete_response)["id"]

    remove_delete = await client.delete(
        _comment_detail_path(workspace_id, case_id, remove_id),
        headers=headers,
    )
    assert remove_delete.status_code == 200

    list_response = await client.get(
        _comments_path(workspace_id, case_id),
        headers=headers,
    )
    assert list_response.status_code == 200
    items = response_data(list_response)
    assert len(items) == 1
    assert items[0]["id"] == keep_id


async def test_delete_comment_not_found_returns_404(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"comment-delete-missing-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Comment Delete Missing",
    )
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.delete(
        _comment_detail_path(workspace_id, case_id, str(uuid.uuid4())),
        headers=headers,
    )
    assert response.status_code == 404


async def test_delete_comment_from_other_case_returns_404(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"comment-delete-other-case-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Comment Delete Other Case",
    )
    case_a = await _create_case(client, headers, workspace_id, title="Case A")
    case_b = await _create_case(client, headers, workspace_id, title="Case B")

    create_response = await _create_comment(
        client,
        headers,
        workspace_id,
        case_b,
        body="Comment on case B",
    )
    assert create_response.status_code == 201
    comment_id = response_data(create_response)["id"]

    response = await client.delete(
        _comment_detail_path(workspace_id, case_a, comment_id),
        headers=headers,
    )
    assert response.status_code == 404


async def test_delete_comment_from_other_workspace_returns_404(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"comment-delete-other-ws-{uuid.uuid4()}@example.com",
    )
    workspace_a = await _create_workspace(client, headers, "Comment Delete WS A")
    workspace_b = await _create_workspace(client, headers, "Comment Delete WS B")
    case_a = await _create_case(client, headers, workspace_a)

    create_response = await _create_comment(
        client,
        headers,
        workspace_a,
        case_a,
        body="Comment in workspace A",
    )
    assert create_response.status_code == 201
    comment_id = response_data(create_response)["id"]

    other_case = UniversalCase(
        workspace_id=UUID(workspace_b),
        title="Case in B",
        status=CaseStatus.OPEN,
    )
    db_session.add(other_case)
    await db_session.flush()
    db_session.add(
        CaseComment(
            workspace_id=UUID(workspace_b),
            case_id=other_case.id,
            body="Comment in workspace B",
        )
    )
    await db_session.flush()

    response = await client.delete(
        _comment_detail_path(workspace_b, str(other_case.id), comment_id),
        headers=headers,
    )
    assert response.status_code == 404


async def test_delete_comment_cross_workspace_case_returns_404(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"comment-delete-cross-{uuid.uuid4()}@example.com",
    )
    workspace_a = await _create_workspace(client, headers, "Comment Delete Cross A")
    workspace_b = await _create_workspace(client, headers, "Comment Delete Cross B")
    case_id = await _create_case(client, headers, workspace_a)
    create_response = await _create_comment(client, headers, workspace_a, case_id)
    comment_id = response_data(create_response)["id"]

    response = await client.delete(
        _comment_detail_path(workspace_b, case_id, comment_id),
        headers=headers,
    )
    assert response.status_code == 404


async def test_delete_comment_non_member_returns_404(client: AsyncClient) -> None:
    owner_email = f"comment-delete-owner-{uuid.uuid4()}@example.com"
    other_email = f"comment-delete-other-{uuid.uuid4()}@example.com"
    owner_headers = await auth_headers(client, owner_email)
    workspace_id = await _create_workspace(
        client,
        owner_headers,
        "Comment Delete Private",
    )
    case_id = await _create_case(client, owner_headers, workspace_id)
    create_response = await _create_comment(
        client,
        owner_headers,
        workspace_id,
        case_id,
    )
    comment_id = response_data(create_response)["id"]

    await register_user(client, email=other_email)
    other_headers = {
        "Authorization": f"Bearer {await login_user(client, email=other_email)}"
    }
    response = await client.delete(
        _comment_detail_path(workspace_id, case_id, comment_id),
        headers=other_headers,
    )
    assert response.status_code == 404


async def test_delete_comment_repeated_delete_returns_404(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"comment-delete-repeat-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Comment Delete Repeat",
    )
    case_id = await _create_case(client, headers, workspace_id)
    create_response = await _create_comment(client, headers, workspace_id, case_id)
    comment_id = response_data(create_response)["id"]

    first_delete = await client.delete(
        _comment_detail_path(workspace_id, case_id, comment_id),
        headers=headers,
    )
    assert first_delete.status_code == 200

    second_delete = await client.delete(
        _comment_detail_path(workspace_id, case_id, comment_id),
        headers=headers,
    )
    assert second_delete.status_code == 404
