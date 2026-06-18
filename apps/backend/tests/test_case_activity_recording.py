"""Tests for automatic Universal Case activity recording."""

import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_activity import CaseActivity
from app.models.enums import (
    CaseActivityType,
    CasePriority,
    CaseStatus,
    WorkspaceMemberRole,
    WorkspaceMemberStatus,
)
from app.models.user import User
from app.models.workspace_membership import WorkspaceMembership
from tests.conftest import auth_headers, login_user, register_user, response_data

pytestmark = pytest.mark.asyncio


def _case_path(workspace_id: str, case_id: str) -> str:
    return f"/api/v1/workspaces/{workspace_id}/cases/{case_id}"


def _comments_path(workspace_id: str, case_id: str) -> str:
    return f"{_case_path(workspace_id, case_id)}/comments"


def _activities_path(workspace_id: str, case_id: str) -> str:
    return f"{_case_path(workspace_id, case_id)}/activities"


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
    title: str = "Activity recording case",
    status: CaseStatus = CaseStatus.OPEN,
) -> str:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": title, "status": status.value},
        headers=headers,
    )
    assert response.status_code == 201
    return response_data(response)["id"]


async def _get_user_id(client: AsyncClient, headers: dict[str, str]) -> str:
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    return response_data(response)["id"]


async def _add_active_workspace_member(
    db_session: AsyncSession,
    workspace_id: str,
    *,
    email: str,
    client: AsyncClient,
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


async def _activity_count(
    db_session: AsyncSession,
    workspace_id: str,
    case_id: str,
) -> int:
    count = await db_session.scalar(
        select(func.count())
        .select_from(CaseActivity)
        .where(
            CaseActivity.workspace_id == UUID(workspace_id),
            CaseActivity.case_id == UUID(case_id),
        )
    )
    return int(count or 0)


async def _list_activities(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: str,
    case_id: str,
) -> list[dict]:
    response = await client.get(
        _activities_path(workspace_id, case_id),
        headers=headers,
    )
    assert response.status_code == 200
    return response_data(response)


async def test_create_case_records_case_created_activity(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"activity-create-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Activity Create Workspace")
    user_id = await _get_user_id(client, headers)

    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={
            "title": "New support case",
            "status": CaseStatus.OPEN.value,
            "priority": CasePriority.HIGH.value,
            "source": "email",
        },
        headers=headers,
    )
    assert response.status_code == 201
    case = response_data(response)

    activities = await _list_activities(client, headers, workspace_id, case["id"])
    assert len(activities) == 1
    activity = activities[0]
    assert activity["workspace_id"] == workspace_id
    assert activity["case_id"] == case["id"]
    assert activity["actor_user_id"] == user_id
    assert activity["activity_type"] == CaseActivityType.CASE_CREATED.value
    assert activity["message"] == "Case created"
    assert activity["metadata"] == {
        "title": "New support case",
        "status": CaseStatus.OPEN.value,
        "priority": CasePriority.HIGH.value,
        "source": "email",
    }
    assert activity["created_at"]


async def test_patch_status_change_records_status_changed_activity(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"activity-status-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Activity Status Workspace")
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        _case_path(workspace_id, case_id),
        json={"status": CaseStatus.PENDING.value},
        headers=headers,
    )
    assert response.status_code == 200

    activities = await _list_activities(client, headers, workspace_id, case_id)
    status_activities = [
        item
        for item in activities
        if item["activity_type"] == CaseActivityType.STATUS_CHANGED.value
    ]
    assert len(status_activities) == 1
    assert status_activities[0]["message"] == "Status changed"
    assert status_activities[0]["metadata"] == {
        "from": CaseStatus.OPEN.value,
        "to": CaseStatus.PENDING.value,
    }


async def test_patch_priority_change_records_priority_changed_activity(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client, f"activity-priority-{uuid.uuid4()}@example.com"
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Activity Priority Workspace",
    )
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        _case_path(workspace_id, case_id),
        json={"priority": CasePriority.URGENT.value},
        headers=headers,
    )
    assert response.status_code == 200

    activities = await _list_activities(client, headers, workspace_id, case_id)
    priority_activities = [
        item
        for item in activities
        if item["activity_type"] == CaseActivityType.PRIORITY_CHANGED.value
    ]
    assert len(priority_activities) == 1
    assert priority_activities[0]["message"] == "Priority changed"
    assert priority_activities[0]["metadata"] == {
        "from": CasePriority.NORMAL.value,
        "to": CasePriority.URGENT.value,
    }


async def test_patch_assign_user_records_assignment_changed_activity(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"activity-assign-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Activity Assign Workspace")
    case_id = await _create_case(client, headers, workspace_id)
    user_id = await _get_user_id(client, headers)

    response = await client.patch(
        _case_path(workspace_id, case_id),
        json={"assigned_to_user_id": user_id},
        headers=headers,
    )
    assert response.status_code == 200

    activities = await _list_activities(client, headers, workspace_id, case_id)
    assignment_activities = [
        item
        for item in activities
        if item["activity_type"] == CaseActivityType.ASSIGNMENT_CHANGED.value
    ]
    assert len(assignment_activities) == 1
    assert assignment_activities[0]["message"] == "Case assigned"
    assert assignment_activities[0]["metadata"] == {"from": None, "to": user_id}


async def test_patch_unassign_user_records_assignment_changed_activity(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client, f"activity-unassign-{uuid.uuid4()}@example.com"
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Activity Unassign Workspace",
    )
    case_id = await _create_case(client, headers, workspace_id)
    user_id = await _get_user_id(client, headers)

    assign_response = await client.patch(
        _case_path(workspace_id, case_id),
        json={"assigned_to_user_id": user_id},
        headers=headers,
    )
    assert assign_response.status_code == 200

    response = await client.patch(
        _case_path(workspace_id, case_id),
        json={"assigned_to_user_id": None},
        headers=headers,
    )
    assert response.status_code == 200

    activities = await _list_activities(client, headers, workspace_id, case_id)
    unassign_activities = [
        item
        for item in activities
        if item["activity_type"] == CaseActivityType.ASSIGNMENT_CHANGED.value
        and item["message"] == "Case unassigned"
    ]
    assert len(unassign_activities) == 1
    assert unassign_activities[0]["metadata"] == {"from": user_id, "to": None}


async def test_patch_reassign_user_records_assignment_changed_activity(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_email = f"activity-reassign-owner-{uuid.uuid4()}@example.com"
    member_email = f"activity-reassign-member-{uuid.uuid4()}@example.com"
    headers = await auth_headers(client, owner_email)
    workspace_id = await _create_workspace(
        client, headers, "Activity Reassign Workspace"
    )
    case_id = await _create_case(client, headers, workspace_id)
    owner_id = await _get_user_id(client, headers)
    member_id = await _add_active_workspace_member(
        db_session,
        workspace_id,
        email=member_email,
        client=client,
    )

    first_assign = await client.patch(
        _case_path(workspace_id, case_id),
        json={"assigned_to_user_id": owner_id},
        headers=headers,
    )
    assert first_assign.status_code == 200

    response = await client.patch(
        _case_path(workspace_id, case_id),
        json={"assigned_to_user_id": member_id},
        headers=headers,
    )
    assert response.status_code == 200

    activities = await _list_activities(client, headers, workspace_id, case_id)
    reassign_activities = [
        item
        for item in activities
        if item["activity_type"] == CaseActivityType.ASSIGNMENT_CHANGED.value
        and item["message"] == "Case reassigned"
    ]
    assert len(reassign_activities) == 1
    assert reassign_activities[0]["metadata"] == {
        "from": owner_id,
        "to": member_id,
    }


async def test_patch_generic_fields_records_case_updated_activity(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"activity-updated-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(
        client, headers, "Activity Updated Workspace"
    )
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        _case_path(workspace_id, case_id),
        json={
            "title": "Updated title",
            "description": "Updated description",
            "customer_name": "Nino",
        },
        headers=headers,
    )
    assert response.status_code == 200

    activities = await _list_activities(client, headers, workspace_id, case_id)
    updated_activities = [
        item
        for item in activities
        if item["activity_type"] == CaseActivityType.CASE_UPDATED.value
    ]
    assert len(updated_activities) == 1
    assert updated_activities[0]["message"] == "Case updated"
    assert set(updated_activities[0]["metadata"]["changed_fields"]) == {
        "title",
        "description",
        "customer_name",
    }


async def test_patch_identical_values_records_no_new_activity(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(client, f"activity-noop-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Activity Noop Workspace")
    case_id = await _create_case(client, headers, workspace_id)
    before_count = await _activity_count(db_session, workspace_id, case_id)

    response = await client.patch(
        _case_path(workspace_id, case_id),
        json={"status": CaseStatus.OPEN.value},
        headers=headers,
    )
    assert response.status_code == 200
    assert await _activity_count(db_session, workspace_id, case_id) == before_count


async def test_patch_status_only_does_not_record_case_updated(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"activity-status-only-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Activity Status Only Workspace",
    )
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        _case_path(workspace_id, case_id),
        json={"status": CaseStatus.RESOLVED.value},
        headers=headers,
    )
    assert response.status_code == 200

    activities = await _list_activities(client, headers, workspace_id, case_id)
    patch_activities = [
        item
        for item in activities
        if item["activity_type"]
        in {
            CaseActivityType.STATUS_CHANGED.value,
            CaseActivityType.CASE_UPDATED.value,
        }
    ]
    assert len(patch_activities) == 1
    assert patch_activities[0]["activity_type"] == CaseActivityType.STATUS_CHANGED.value


async def test_patch_status_and_title_records_both_activities(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"activity-status-title-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Activity Status Title Workspace",
    )
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.patch(
        _case_path(workspace_id, case_id),
        json={
            "status": CaseStatus.PENDING.value,
            "title": "Renamed case",
        },
        headers=headers,
    )
    assert response.status_code == 200

    activities = await _list_activities(client, headers, workspace_id, case_id)
    patch_types = {
        item["activity_type"]
        for item in activities
        if item["activity_type"]
        in {
            CaseActivityType.STATUS_CHANGED.value,
            CaseActivityType.CASE_UPDATED.value,
        }
    }
    assert patch_types == {
        CaseActivityType.STATUS_CHANGED.value,
        CaseActivityType.CASE_UPDATED.value,
    }
    updated = next(
        item
        for item in activities
        if item["activity_type"] == CaseActivityType.CASE_UPDATED.value
    )
    assert updated["metadata"]["changed_fields"] == ["title"]


async def test_create_comment_records_comment_created_activity(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"activity-comment-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(
        client, headers, "Activity Comment Workspace"
    )
    case_id = await _create_case(client, headers, workspace_id)

    response = await client.post(
        _comments_path(workspace_id, case_id),
        json={"body": "Customer called back", "is_internal": False},
        headers=headers,
    )
    assert response.status_code == 201
    comment = response_data(response)

    activities = await _list_activities(client, headers, workspace_id, case_id)
    comment_activities = [
        item
        for item in activities
        if item["activity_type"] == CaseActivityType.COMMENT_CREATED.value
    ]
    assert len(comment_activities) == 1
    assert comment_activities[0]["message"] == "Comment added"
    assert comment_activities[0]["metadata"] == {
        "comment_id": comment["id"],
        "is_internal": False,
    }


async def test_delete_comment_records_comment_deleted_activity(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"activity-comment-delete-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Activity Comment Delete Workspace",
    )
    case_id = await _create_case(client, headers, workspace_id)

    create_response = await client.post(
        _comments_path(workspace_id, case_id),
        json={"body": "Delete me"},
        headers=headers,
    )
    assert create_response.status_code == 201
    comment = response_data(create_response)

    delete_response = await client.delete(
        f"{_comments_path(workspace_id, case_id)}/{comment['id']}",
        headers=headers,
    )
    assert delete_response.status_code == 200

    activities = await _list_activities(client, headers, workspace_id, case_id)
    deleted_activities = [
        item
        for item in activities
        if item["activity_type"] == CaseActivityType.COMMENT_DELETED.value
    ]
    assert len(deleted_activities) == 1
    assert deleted_activities[0]["message"] == "Comment deleted"
    assert deleted_activities[0]["metadata"] == {
        "comment_id": comment["id"],
        "is_internal": True,
    }


async def test_failed_non_member_patch_does_not_record_activity(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_email = f"activity-fail-owner-{uuid.uuid4()}@example.com"
    other_email = f"activity-fail-other-{uuid.uuid4()}@example.com"
    owner_headers = await auth_headers(client, owner_email)
    workspace_id = await _create_workspace(
        client, owner_headers, "Activity Fail Workspace"
    )
    case_id = await _create_case(client, owner_headers, workspace_id)
    before_count = await _activity_count(db_session, workspace_id, case_id)

    await register_user(client, email=other_email)
    other_headers = {
        "Authorization": f"Bearer {await login_user(client, email=other_email)}"
    }
    response = await client.patch(
        _case_path(workspace_id, case_id),
        json={"title": "Should not apply"},
        headers=other_headers,
    )
    assert response.status_code == 404
    assert await _activity_count(db_session, workspace_id, case_id) == before_count


async def test_failed_cross_workspace_patch_does_not_record_activity(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(client, f"activity-cross-{uuid.uuid4()}@example.com")
    workspace_a = await _create_workspace(client, headers, "Activity Cross A")
    workspace_b = await _create_workspace(client, headers, "Activity Cross B")
    case_id = await _create_case(client, headers, workspace_a)
    before_count = await _activity_count(db_session, workspace_a, case_id)

    response = await client.patch(
        _case_path(workspace_b, case_id),
        json={"title": "Cross workspace"},
        headers=headers,
    )
    assert response.status_code == 404
    assert await _activity_count(db_session, workspace_a, case_id) == before_count


async def test_failed_unauthenticated_patch_does_not_record_activity(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(client, f"activity-unauth-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Activity Unauth Workspace")
    case_id = await _create_case(client, headers, workspace_id)
    before_count = await _activity_count(db_session, workspace_id, case_id)

    response = await client.patch(
        _case_path(workspace_id, case_id),
        json={"title": "No auth"},
    )
    assert response.status_code == 401
    assert await _activity_count(db_session, workspace_id, case_id) == before_count


async def test_activity_list_returns_recorded_timeline_newest_first(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client, f"activity-timeline-{uuid.uuid4()}@example.com"
    )
    workspace_id = await _create_workspace(
        client, headers, "Activity Timeline Workspace"
    )
    case_id = await _create_case(client, headers, workspace_id)

    await client.patch(
        _case_path(workspace_id, case_id),
        json={"status": CaseStatus.PENDING.value},
        headers=headers,
    )
    comment_response = await client.post(
        _comments_path(workspace_id, case_id),
        json={"body": "Follow up"},
        headers=headers,
    )
    assert comment_response.status_code == 201

    result = await db_session.scalars(
        select(CaseActivity).where(
            CaseActivity.workspace_id == UUID(workspace_id),
            CaseActivity.case_id == UUID(case_id),
        )
    )
    activities_by_type = {activity.activity_type: activity for activity in result.all()}
    activities_by_type[CaseActivityType.CASE_CREATED].created_at = datetime.now(
        UTC
    ) - timedelta(hours=2)
    activities_by_type[CaseActivityType.STATUS_CHANGED].created_at = datetime.now(
        UTC
    ) - timedelta(hours=1)
    activities_by_type[CaseActivityType.COMMENT_CREATED].created_at = datetime.now(UTC)
    await db_session.flush()

    activities = await _list_activities(client, headers, workspace_id, case_id)
    assert len(activities) == 3
    assert activities[0]["activity_type"] == CaseActivityType.COMMENT_CREATED.value
    assert activities[1]["activity_type"] == CaseActivityType.STATUS_CHANGED.value
    assert activities[2]["activity_type"] == CaseActivityType.CASE_CREATED.value
