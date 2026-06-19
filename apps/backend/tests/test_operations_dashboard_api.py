"""Tests for Operations Dashboard API."""

import uuid
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_case_metric import AgentCaseMetric
from app.models.case_qa_review import CaseQaReview
from app.models.enums import (
    CaseStatus,
    QaReviewStatus,
    SlaStatus,
    UserStatus,
    WorkspaceMemberRole,
    WorkspaceMemberStatus,
    WorkspaceStatus,
)
from app.models.universal_case import UniversalCase
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_membership import WorkspaceMembership
from app.services.agent_workforce_service import clock_in
from app.services.case_qa_service import create_qa_review
from tests.conftest import auth_headers, register_user, response_data

pytestmark = pytest.mark.asyncio


def _dashboard_path(workspace_id: str) -> str:
    return f"/api/v1/workspaces/{workspace_id}/operations/dashboard"


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


async def _get_dashboard(
    client: AsyncClient,
    *,
    url: str,
    headers: dict[str, str],
) -> dict:
    response = await client.get(url, headers=headers)
    assert response.status_code == 200
    return response_data(response)


async def _create_workspace_with_owner(
    db_session: AsyncSession,
    *,
    name_suffix: str,
) -> tuple[Workspace, User]:
    user = User(
        email=f"ops-owner-{name_suffix}@example.com",
        password_hash="hashed-password",
        status=UserStatus.ACTIVE,
    )
    workspace = Workspace(
        name=f"Ops Workspace {name_suffix}",
        slug=f"ops-workspace-{name_suffix}",
        status=WorkspaceStatus.ACTIVE,
    )
    db_session.add_all([user, workspace])
    await db_session.flush()
    db_session.add(
        WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=user.id,
            role=WorkspaceMemberRole.OWNER,
            status=WorkspaceMemberStatus.ACTIVE,
        )
    )
    await db_session.flush()
    return workspace, user


async def test_operations_dashboard_unauthenticated_returns_401(
    client: AsyncClient,
) -> None:
    response = await client.get(
        _dashboard_path(str(uuid.uuid4())),
    )
    assert response.status_code == 401


async def test_operations_dashboard_non_member_returns_404(
    client: AsyncClient,
) -> None:
    owner_headers = await auth_headers(
        client,
        f"ops-owner-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        owner_headers,
        "Private Ops Workspace",
    )
    other_headers = await auth_headers(
        client,
        f"ops-other-{uuid.uuid4()}@example.com",
    )

    response = await client.get(
        _dashboard_path(workspace_id),
        headers=other_headers,
    )
    assert response.status_code == 404


async def test_operations_dashboard_empty_workspace_returns_zero_counts(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(client, f"ops-empty-{uuid.uuid4()}@example.com")
    workspace_id = await _create_workspace(client, headers, "Empty Ops Workspace")

    dashboard = await _get_dashboard(
        client,
        url=_dashboard_path(workspace_id),
        headers=headers,
    )

    assert dashboard["cases"] == {
        "total_cases": 0,
        "open_cases": 0,
        "pending_cases": 0,
        "resolved_cases": 0,
    }
    assert dashboard["sla"] == {
        "on_track": 0,
        "at_risk": 0,
        "breached": 0,
    }
    assert dashboard["agents"] == {
        "active_shifts": 0,
        "total_agent_case_metrics": 0,
        "total_agent_messages": 0,
    }
    assert dashboard["qa"] == {
        "total_reviews": 0,
        "pending_reviews": 0,
        "approved_reviews": 0,
        "rejected_reviews": 0,
        "average_score": 0.0,
    }


async def test_operations_dashboard_counts_cases_by_status(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    suffix = uuid.uuid4().hex[:12]
    headers = await auth_headers(client, f"ops-cases-{suffix}@example.com")
    workspace_id = await _create_workspace(client, headers, "Case Count Workspace")
    user = await db_session.scalar(
        select(User).where(User.email == f"ops-cases-{suffix}@example.com")
    )
    assert user is not None

    for title, status in (
        ("Open case", CaseStatus.OPEN),
        ("Pending case", CaseStatus.PENDING),
        ("Resolved case", CaseStatus.RESOLVED),
        ("Closed case", CaseStatus.CLOSED),
    ):
        db_session.add(
            UniversalCase(
                workspace_id=UUID(workspace_id),
                title=title,
                status=status,
                created_by_user_id=user.id,
            )
        )
    await db_session.flush()

    dashboard = await _get_dashboard(
        client,
        url=_dashboard_path(workspace_id),
        headers=headers,
    )

    assert dashboard["cases"]["total_cases"] == 4
    assert dashboard["cases"]["open_cases"] == 1
    assert dashboard["cases"]["pending_cases"] == 1
    assert dashboard["cases"]["resolved_cases"] == 1


async def test_operations_dashboard_counts_sla_statuses(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    suffix = uuid.uuid4().hex[:12]
    headers = await auth_headers(client, f"ops-sla-{suffix}@example.com")
    workspace_id = await _create_workspace(client, headers, "SLA Count Workspace")
    user = await db_session.scalar(
        select(User).where(User.email == f"ops-sla-{suffix}@example.com")
    )
    assert user is not None

    for sla_status in (SlaStatus.ON_TRACK, SlaStatus.AT_RISK, SlaStatus.BREACHED):
        db_session.add(
            UniversalCase(
                workspace_id=UUID(workspace_id),
                title=f"SLA {sla_status.value}",
                status=CaseStatus.OPEN,
                sla_status=sla_status,
                created_by_user_id=user.id,
            )
        )
    await db_session.flush()

    dashboard = await _get_dashboard(
        client,
        url=_dashboard_path(workspace_id),
        headers=headers,
    )

    assert dashboard["sla"] == {
        "on_track": 1,
        "at_risk": 1,
        "breached": 1,
    }


async def test_operations_dashboard_counts_active_shifts_and_agent_messages(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    suffix = uuid.uuid4().hex[:12]
    headers = await auth_headers(client, f"ops-agents-{suffix}@example.com")
    workspace_id = await _create_workspace(client, headers, "Agent Count Workspace")
    user = await db_session.scalar(
        select(User).where(User.email == f"ops-agents-{suffix}@example.com")
    )
    assert user is not None

    case = UniversalCase(
        workspace_id=UUID(workspace_id),
        title="Agent metrics case",
        status=CaseStatus.OPEN,
        created_by_user_id=user.id,
    )
    db_session.add(case)
    await db_session.flush()

    await clock_in(db_session, user.id, UUID(workspace_id))
    db_session.add(
        AgentCaseMetric(
            workspace_id=UUID(workspace_id),
            case_id=case.id,
            user_id=user.id,
            messages_count=3,
        )
    )
    db_session.add(
        AgentCaseMetric(
            workspace_id=UUID(workspace_id),
            case_id=case.id,
            user_id=user.id,
            messages_count=2,
        )
    )
    await db_session.flush()

    dashboard = await _get_dashboard(
        client,
        url=_dashboard_path(workspace_id),
        headers=headers,
    )

    assert dashboard["agents"]["active_shifts"] == 1
    assert dashboard["agents"]["total_agent_case_metrics"] == 2
    assert dashboard["agents"]["total_agent_messages"] == 5


async def test_operations_dashboard_counts_qa_statuses_and_average_score(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    suffix = uuid.uuid4().hex[:12]
    headers = await auth_headers(client, f"ops-qa-{suffix}@example.com")
    workspace_id = await _create_workspace(client, headers, "QA Count Workspace")
    owner = await db_session.scalar(
        select(User).where(User.email == f"ops-qa-{suffix}@example.com")
    )
    assert owner is not None

    await register_user(
        client,
        email=f"ops-agent-{suffix}@example.com",
    )
    agent = await db_session.scalar(
        select(User).where(User.email == f"ops-agent-{suffix}@example.com")
    )
    assert agent is not None

    case = UniversalCase(
        workspace_id=UUID(workspace_id),
        title="QA dashboard case",
        status=CaseStatus.OPEN,
        created_by_user_id=owner.id,
    )
    db_session.add(case)
    await db_session.flush()

    pending = await create_qa_review(db_session, case.id, owner.id, agent.id)
    approved = await create_qa_review(db_session, case.id, owner.id, agent.id)
    rejected = await create_qa_review(db_session, case.id, owner.id, agent.id)
    approved.status = QaReviewStatus.APPROVED
    approved.score = 80
    rejected.status = QaReviewStatus.REJECTED
    rejected.score = 60
    pending.score = 40
    await db_session.flush()

    dashboard = await _get_dashboard(
        client,
        url=_dashboard_path(workspace_id),
        headers=headers,
    )

    assert dashboard["qa"]["total_reviews"] == 3
    assert dashboard["qa"]["pending_reviews"] == 1
    assert dashboard["qa"]["approved_reviews"] == 1
    assert dashboard["qa"]["rejected_reviews"] == 1
    assert dashboard["qa"]["average_score"] == 60.0


async def test_operations_dashboard_excludes_other_workspace_data(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    suffix = uuid.uuid4().hex[:12]
    headers = await auth_headers(client, f"ops-iso-{suffix}@example.com")
    workspace_a_id = await _create_workspace(client, headers, "Ops Workspace A")
    owner = await db_session.scalar(
        select(User).where(User.email == f"ops-iso-{suffix}@example.com")
    )
    assert owner is not None

    workspace_b, agent = await _create_workspace_with_owner(
        db_session,
        name_suffix=f"b-{suffix}",
    )
    case_b = UniversalCase(
        workspace_id=workspace_b.id,
        title="Other workspace case",
        status=CaseStatus.OPEN,
        sla_status=SlaStatus.BREACHED,
        created_by_user_id=agent.id,
    )
    db_session.add(case_b)
    await db_session.flush()
    await clock_in(db_session, agent.id, workspace_b.id)
    db_session.add(
        AgentCaseMetric(
            workspace_id=workspace_b.id,
            case_id=case_b.id,
            user_id=agent.id,
            messages_count=7,
        )
    )
    db_session.add(
        CaseQaReview(
            workspace_id=workspace_b.id,
            case_id=case_b.id,
            reviewed_by_user_id=agent.id,
            reviewed_agent_user_id=agent.id,
            score=90,
            status=QaReviewStatus.APPROVED,
        )
    )
    await db_session.flush()

    db_session.add(
        UniversalCase(
            workspace_id=UUID(workspace_a_id),
            title="Workspace A case",
            status=CaseStatus.OPEN,
            sla_status=SlaStatus.ON_TRACK,
            created_by_user_id=owner.id,
        )
    )
    await db_session.flush()

    dashboard = await _get_dashboard(
        client,
        url=_dashboard_path(workspace_a_id),
        headers=headers,
    )

    assert dashboard["cases"]["total_cases"] == 1
    assert dashboard["sla"]["breached"] == 0
    assert dashboard["agents"]["active_shifts"] == 0
    assert dashboard["agents"]["total_agent_messages"] == 0
    assert dashboard["qa"]["total_reviews"] == 0
