"""Tests for Case QA review API."""

import uuid
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import (
    QaReviewStatus,
    WorkspaceMemberRole,
    WorkspaceMemberStatus,
)
from app.models.workspace_membership import WorkspaceMembership
from tests.conftest import auth_headers, login_user, register_user, response_data

pytestmark = pytest.mark.asyncio


def _qa_reviews_path(workspace_id: str, case_id: str) -> str:
    return f"/api/v1/workspaces/{workspace_id}/cases/{case_id}/qa-reviews"


def _qa_review_criteria_path(
    workspace_id: str,
    case_id: str,
    review_id: str,
) -> str:
    return f"{_qa_reviews_path(workspace_id, case_id)}/{review_id}/criteria"


def _qa_review_approve_path(
    workspace_id: str,
    case_id: str,
    review_id: str,
) -> str:
    return f"{_qa_reviews_path(workspace_id, case_id)}/{review_id}/approve"


def _qa_review_reject_path(
    workspace_id: str,
    case_id: str,
    review_id: str,
) -> str:
    return f"{_qa_reviews_path(workspace_id, case_id)}/{review_id}/reject"


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
    title: str = "QA test case",
) -> str:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": title},
        headers=headers,
    )
    assert response.status_code == 201
    return response_data(response)["id"]


async def _register_agent_member(
    client: AsyncClient,
    db_session: AsyncSession,
    workspace_id: str,
) -> tuple[str, dict[str, str]]:
    agent_email = f"qa-agent-{uuid.uuid4()}@example.com"
    await register_user(client, email=agent_email)
    agent_headers = {
        "Authorization": f"Bearer {await login_user(client, email=agent_email)}"
    }
    me_response = await client.get("/api/v1/auth/me", headers=agent_headers)
    agent_user_id = UUID(response_data(me_response)["id"])

    db_session.add(
        WorkspaceMembership(
            workspace_id=UUID(workspace_id),
            user_id=agent_user_id,
            role=WorkspaceMemberRole.MEMBER,
            status=WorkspaceMemberStatus.ACTIVE,
        )
    )
    await db_session.flush()
    return str(agent_user_id), agent_headers


async def _create_qa_review(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: str,
    case_id: str,
    *,
    reviewed_agent_user_id: str,
    overall_comment: str | None = None,
) -> dict:
    payload: dict[str, object] = {
        "reviewed_agent_user_id": reviewed_agent_user_id,
    }
    if overall_comment is not None:
        payload["overall_comment"] = overall_comment
    response = await client.post(
        _qa_reviews_path(workspace_id, case_id),
        json=payload,
        headers=headers,
    )
    return response


async def test_list_qa_reviews_unauthenticated_returns_401(
    client: AsyncClient,
) -> None:
    response = await client.get(
        _qa_reviews_path(str(uuid.uuid4()), str(uuid.uuid4())),
    )
    assert response.status_code == 401


async def test_create_qa_review_unauthenticated_returns_401(
    client: AsyncClient,
) -> None:
    response = await client.post(
        _qa_reviews_path(str(uuid.uuid4()), str(uuid.uuid4())),
        json={"reviewed_agent_user_id": str(uuid.uuid4())},
    )
    assert response.status_code == 401


async def test_list_qa_reviews_non_member_returns_404(client: AsyncClient) -> None:
    owner_headers = await _auth("qa-owner-list", client)
    workspace_id = await _create_workspace(client, owner_headers, "QA Private List")
    case_id = await _create_case(client, owner_headers, workspace_id)

    other_headers = await _auth("qa-other-list", client)
    response = await client.get(
        _qa_reviews_path(workspace_id, case_id),
        headers=other_headers,
    )
    assert response.status_code == 404


async def test_create_qa_review_non_member_returns_404(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_headers = await _auth("qa-owner-create", client)
    workspace_id = await _create_workspace(client, owner_headers, "QA Private Create")
    case_id = await _create_case(client, owner_headers, workspace_id)
    agent_id, _ = await _register_agent_member(client, db_session, workspace_id)

    other_headers = await _auth("qa-other-create", client)
    response = await _create_qa_review(
        client,
        other_headers,
        workspace_id,
        case_id,
        reviewed_agent_user_id=agent_id,
    )
    assert response.status_code == 404


async def test_create_qa_review_as_workspace_member(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_headers = await _auth("qa-create", client)
    workspace_id = await _create_workspace(client, owner_headers, "QA Create Workspace")
    case_id = await _create_case(client, owner_headers, workspace_id)
    agent_id, _ = await _register_agent_member(client, db_session, workspace_id)

    me_response = await client.get("/api/v1/auth/me", headers=owner_headers)
    reviewer_id = response_data(me_response)["id"]

    response = await _create_qa_review(
        client,
        owner_headers,
        workspace_id,
        case_id,
        reviewed_agent_user_id=agent_id,
        overall_comment="Initial QA note",
    )
    assert response.status_code == 201
    data = response_data(response)
    assert data["workspace_id"] == workspace_id
    assert data["case_id"] == case_id
    assert data["reviewed_by_user_id"] == reviewer_id
    assert data["reviewed_agent_user_id"] == agent_id
    assert data["score"] == 0
    assert data["status"] == QaReviewStatus.PENDING.value
    assert data["overall_comment"] == "Initial QA note"
    assert data["criteria_scores"] == []
    assert data["id"]
    assert data["created_at"]
    assert data["updated_at"]


async def test_create_qa_review_reviewed_agent_must_be_active_member(
    client: AsyncClient,
) -> None:
    owner_headers = await _auth("qa-agent-check", client)
    workspace_id = await _create_workspace(client, owner_headers, "QA Agent Check")
    case_id = await _create_case(client, owner_headers, workspace_id)

    outsider_headers = await _auth("qa-outsider", client)
    outsider_id = response_data(
        await client.get("/api/v1/auth/me", headers=outsider_headers)
    )["id"]

    response = await _create_qa_review(
        client,
        owner_headers,
        workspace_id,
        case_id,
        reviewed_agent_user_id=outsider_id,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Assignee must be an active member of this workspace"
    )


async def test_list_qa_reviews_only_returns_reviews_for_case(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_headers = await _auth("qa-list-case", client)
    workspace_id = await _create_workspace(client, owner_headers, "QA List Case")
    case_a = await _create_case(client, owner_headers, workspace_id, title="Case A")
    case_b = await _create_case(client, owner_headers, workspace_id, title="Case B")
    agent_id, _ = await _register_agent_member(client, db_session, workspace_id)

    review_a = await _create_qa_review(
        client,
        owner_headers,
        workspace_id,
        case_a,
        reviewed_agent_user_id=agent_id,
    )
    review_b = await _create_qa_review(
        client,
        owner_headers,
        workspace_id,
        case_b,
        reviewed_agent_user_id=agent_id,
    )
    assert review_a.status_code == 201
    assert review_b.status_code == 201
    review_a_id = response_data(review_a)["id"]

    list_response = await client.get(
        _qa_reviews_path(workspace_id, case_a),
        headers=owner_headers,
    )
    assert list_response.status_code == 200
    items = response_data(list_response)
    assert len(items) == 1
    assert items[0]["id"] == review_a_id
    assert items[0]["case_id"] == case_a


async def test_add_criteria_score_recalculates_final_score(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_headers = await _auth("qa-score", client)
    workspace_id = await _create_workspace(client, owner_headers, "QA Score Workspace")
    case_id = await _create_case(client, owner_headers, workspace_id)
    agent_id, _ = await _register_agent_member(client, db_session, workspace_id)

    create_response = await _create_qa_review(
        client,
        owner_headers,
        workspace_id,
        case_id,
        reviewed_agent_user_id=agent_id,
    )
    assert create_response.status_code == 201
    review_id = response_data(create_response)["id"]

    first_score = await client.post(
        _qa_review_criteria_path(workspace_id, case_id, review_id),
        json={"criterion_name": "Tone", "score": 80},
        headers=owner_headers,
    )
    assert first_score.status_code == 201
    first_data = response_data(first_score)
    assert first_data["score"] == 80
    assert len(first_data["criteria_scores"]) == 1

    second_score = await client.post(
        _qa_review_criteria_path(workspace_id, case_id, review_id),
        json={"criterion_name": "Accuracy", "score": 60},
        headers=owner_headers,
    )
    assert second_score.status_code == 201
    second_data = response_data(second_score)
    assert second_data["score"] == 70
    assert len(second_data["criteria_scores"]) == 2


async def test_approve_qa_review_changes_status(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_headers = await _auth("qa-approve", client)
    workspace_id = await _create_workspace(
        client,
        owner_headers,
        "QA Approve Workspace",
    )
    case_id = await _create_case(client, owner_headers, workspace_id)
    agent_id, _ = await _register_agent_member(client, db_session, workspace_id)

    create_response = await _create_qa_review(
        client,
        owner_headers,
        workspace_id,
        case_id,
        reviewed_agent_user_id=agent_id,
    )
    review_id = response_data(create_response)["id"]

    approve_response = await client.post(
        _qa_review_approve_path(workspace_id, case_id, review_id),
        headers=owner_headers,
    )
    assert approve_response.status_code == 200
    data = response_data(approve_response)
    assert data["status"] == QaReviewStatus.APPROVED.value


async def test_reject_qa_review_changes_status(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_headers = await _auth("qa-reject", client)
    workspace_id = await _create_workspace(client, owner_headers, "QA Reject Workspace")
    case_id = await _create_case(client, owner_headers, workspace_id)
    agent_id, _ = await _register_agent_member(client, db_session, workspace_id)

    create_response = await _create_qa_review(
        client,
        owner_headers,
        workspace_id,
        case_id,
        reviewed_agent_user_id=agent_id,
    )
    review_id = response_data(create_response)["id"]

    reject_response = await client.post(
        _qa_review_reject_path(workspace_id, case_id, review_id),
        headers=owner_headers,
    )
    assert reject_response.status_code == 200
    data = response_data(reject_response)
    assert data["status"] == QaReviewStatus.REJECTED.value


async def test_cannot_approve_non_pending_review(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_headers = await _auth("qa-approve-twice", client)
    workspace_id = await _create_workspace(client, owner_headers, "QA Approve Twice")
    case_id = await _create_case(client, owner_headers, workspace_id)
    agent_id, _ = await _register_agent_member(client, db_session, workspace_id)

    create_response = await _create_qa_review(
        client,
        owner_headers,
        workspace_id,
        case_id,
        reviewed_agent_user_id=agent_id,
    )
    review_id = response_data(create_response)["id"]

    first_approve = await client.post(
        _qa_review_approve_path(workspace_id, case_id, review_id),
        headers=owner_headers,
    )
    assert first_approve.status_code == 200

    second_approve = await client.post(
        _qa_review_approve_path(workspace_id, case_id, review_id),
        headers=owner_headers,
    )
    assert second_approve.status_code == 422
    assert second_approve.json()["detail"] == "Only pending reviews can be approved"


async def test_cannot_reject_non_pending_review(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_headers = await _auth("qa-reject-twice", client)
    workspace_id = await _create_workspace(client, owner_headers, "QA Reject Twice")
    case_id = await _create_case(client, owner_headers, workspace_id)
    agent_id, _ = await _register_agent_member(client, db_session, workspace_id)

    create_response = await _create_qa_review(
        client,
        owner_headers,
        workspace_id,
        case_id,
        reviewed_agent_user_id=agent_id,
    )
    review_id = response_data(create_response)["id"]

    first_reject = await client.post(
        _qa_review_reject_path(workspace_id, case_id, review_id),
        headers=owner_headers,
    )
    assert first_reject.status_code == 200

    second_reject = await client.post(
        _qa_review_reject_path(workspace_id, case_id, review_id),
        headers=owner_headers,
    )
    assert second_reject.status_code == 422
    assert second_reject.json()["detail"] == "Only pending reviews can be rejected"


async def test_cross_workspace_qa_review_access_blocked(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_headers = await _auth("qa-cross-ws", client)
    workspace_a = await _create_workspace(client, owner_headers, "QA Cross A")
    workspace_b = await _create_workspace(client, owner_headers, "QA Cross B")
    case_id = await _create_case(client, owner_headers, workspace_a)
    agent_id, _ = await _register_agent_member(client, db_session, workspace_a)

    create_response = await _create_qa_review(
        client,
        owner_headers,
        workspace_a,
        case_id,
        reviewed_agent_user_id=agent_id,
    )
    review_id = response_data(create_response)["id"]

    approve_response = await client.post(
        _qa_review_approve_path(workspace_b, case_id, review_id),
        headers=owner_headers,
    )
    assert approve_response.status_code == 404

    criteria_response = await client.post(
        _qa_review_criteria_path(workspace_b, case_id, review_id),
        json={"criterion_name": "Tone", "score": 90},
        headers=owner_headers,
    )
    assert criteria_response.status_code == 404


async def test_cross_case_qa_review_access_blocked(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_headers = await _auth("qa-cross-case", client)
    workspace_id = await _create_workspace(client, owner_headers, "QA Cross Case")
    case_a = await _create_case(client, owner_headers, workspace_id, title="Case A")
    case_b = await _create_case(client, owner_headers, workspace_id, title="Case B")
    agent_id, _ = await _register_agent_member(client, db_session, workspace_id)

    create_response = await _create_qa_review(
        client,
        owner_headers,
        workspace_id,
        case_b,
        reviewed_agent_user_id=agent_id,
    )
    review_id = response_data(create_response)["id"]

    approve_response = await client.post(
        _qa_review_approve_path(workspace_id, case_a, review_id),
        headers=owner_headers,
    )
    assert approve_response.status_code == 404

    criteria_response = await client.post(
        _qa_review_criteria_path(workspace_id, case_a, review_id),
        json={"criterion_name": "Tone", "score": 90},
        headers=owner_headers,
    )
    assert criteria_response.status_code == 404


async def test_list_qa_reviews_cross_workspace_returns_404(
    client: AsyncClient,
) -> None:
    owner_headers = await _auth("qa-list-cross-ws", client)
    workspace_a = await _create_workspace(client, owner_headers, "QA List Cross A")
    workspace_b = await _create_workspace(client, owner_headers, "QA List Cross B")
    case_id = await _create_case(client, owner_headers, workspace_a)

    response = await client.get(
        _qa_reviews_path(workspace_b, case_id),
        headers=owner_headers,
    )
    assert response.status_code == 404
