"""Tests for case QA review service and models."""

import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_qa_criteria_score import CaseQaCriteriaScore
from app.models.case_qa_review import CaseQaReview
from app.models.enums import (
    CaseStatus,
    QaReviewStatus,
    UserStatus,
    WorkspaceMemberRole,
    WorkspaceMemberStatus,
    WorkspaceStatus,
)
from app.models.universal_case import UniversalCase
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_membership import WorkspaceMembership
from app.services.case_qa_service import (
    InvalidQaReviewStatusError,
    InvalidQaScoreError,
    add_criteria_score,
    approve_review,
    calculate_final_score,
    create_qa_review,
    reject_review,
)

pytestmark = pytest.mark.asyncio


async def _create_workspace_case_users(
    db_session: AsyncSession,
) -> tuple[Workspace, UniversalCase, User, User]:
    suffix = uuid.uuid4().hex[:12]
    reviewer = User(
        email=f"qa-reviewer-{suffix}@example.com",
        password_hash="hashed-password",
        status=UserStatus.ACTIVE,
    )
    agent = User(
        email=f"qa-agent-{suffix}@example.com",
        password_hash="hashed-password",
        status=UserStatus.ACTIVE,
    )
    workspace = Workspace(
        name=f"QA Workspace {suffix}",
        slug=f"qa-workspace-{suffix}",
        status=WorkspaceStatus.ACTIVE,
    )
    db_session.add_all([reviewer, agent, workspace])
    await db_session.flush()

    db_session.add_all(
        [
            WorkspaceMembership(
                workspace_id=workspace.id,
                user_id=reviewer.id,
                role=WorkspaceMemberRole.OWNER,
                status=WorkspaceMemberStatus.ACTIVE,
            ),
            WorkspaceMembership(
                workspace_id=workspace.id,
                user_id=agent.id,
                role=WorkspaceMemberRole.MEMBER,
                status=WorkspaceMemberStatus.ACTIVE,
            ),
        ]
    )
    await db_session.flush()

    case = UniversalCase(
        workspace_id=workspace.id,
        title="QA evaluation case",
        status=CaseStatus.OPEN,
        created_by_user_id=reviewer.id,
        assigned_to_user_id=agent.id,
    )
    db_session.add(case)
    await db_session.flush()
    return workspace, case, reviewer, agent


async def _create_second_workspace_case(
    db_session: AsyncSession,
    reviewer: User,
) -> tuple[Workspace, UniversalCase]:
    suffix = uuid.uuid4().hex[:12]
    workspace = Workspace(
        name=f"QA Workspace B {suffix}",
        slug=f"qa-workspace-b-{suffix}",
        status=WorkspaceStatus.ACTIVE,
    )
    db_session.add(workspace)
    await db_session.flush()
    db_session.add(
        WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=reviewer.id,
            role=WorkspaceMemberRole.OWNER,
            status=WorkspaceMemberStatus.ACTIVE,
        )
    )
    await db_session.flush()

    case = UniversalCase(
        workspace_id=workspace.id,
        title="Other workspace case",
        status=CaseStatus.OPEN,
        created_by_user_id=reviewer.id,
    )
    db_session.add(case)
    await db_session.flush()
    return workspace, case


async def test_create_qa_review(db_session: AsyncSession) -> None:
    workspace, case, reviewer, agent = await _create_workspace_case_users(db_session)

    review = await create_qa_review(
        db_session,
        case.id,
        reviewer.id,
        agent.id,
    )

    assert review.workspace_id == workspace.id
    assert review.case_id == case.id
    assert review.reviewed_by_user_id == reviewer.id
    assert review.reviewed_agent_user_id == agent.id
    assert review.status == QaReviewStatus.PENDING
    assert review.score == 0


async def test_add_multiple_criteria_scores_recalculates_final_score(
    db_session: AsyncSession,
) -> None:
    _workspace, case, reviewer, agent = await _create_workspace_case_users(db_session)
    review = await create_qa_review(db_session, case.id, reviewer.id, agent.id)

    await add_criteria_score(
        db_session,
        review.id,
        "tone",
        80,
        comment="Professional",
    )
    await add_criteria_score(
        db_session,
        review.id,
        "accuracy",
        90,
        comment="Correct information",
    )
    await add_criteria_score(
        db_session,
        review.id,
        "resolution",
        70,
    )

    await db_session.refresh(review)
    assert review.score == 80

    criteria_count = await db_session.scalar(
        select(func.count())
        .select_from(CaseQaCriteriaScore)
        .where(CaseQaCriteriaScore.qa_review_id == review.id)
    )
    assert criteria_count == 3


async def test_calculate_final_score_rounds_average(
    db_session: AsyncSession,
) -> None:
    _workspace, case, reviewer, agent = await _create_workspace_case_users(db_session)
    review = await create_qa_review(db_session, case.id, reviewer.id, agent.id)

    await add_criteria_score(db_session, review.id, "tone", 85)
    await add_criteria_score(db_session, review.id, "accuracy", 86)

    final_score = await calculate_final_score(db_session, review.id)
    assert final_score == 86


async def test_approve_and_reject_transitions(
    db_session: AsyncSession,
) -> None:
    _workspace, case, reviewer, agent = await _create_workspace_case_users(db_session)
    review = await create_qa_review(db_session, case.id, reviewer.id, agent.id)

    approved = await approve_review(db_session, review.id)
    assert approved.status == QaReviewStatus.APPROVED

    with pytest.raises(InvalidQaReviewStatusError):
        await reject_review(db_session, review.id)


async def test_reject_review_from_pending(db_session: AsyncSession) -> None:
    _workspace, case, reviewer, agent = await _create_workspace_case_users(db_session)
    review = await create_qa_review(db_session, case.id, reviewer.id, agent.id)

    rejected = await reject_review(db_session, review.id)
    assert rejected.status == QaReviewStatus.REJECTED


async def test_cascade_delete_removes_reviews_and_criteria(
    db_session: AsyncSession,
) -> None:
    _workspace, case, reviewer, agent = await _create_workspace_case_users(db_session)
    review = await create_qa_review(db_session, case.id, reviewer.id, agent.id)
    await add_criteria_score(db_session, review.id, "tone", 75)

    await db_session.delete(case)
    await db_session.flush()

    assert await db_session.get(CaseQaReview, review.id) is None
    criteria_count = await db_session.scalar(
        select(func.count()).select_from(CaseQaCriteriaScore)
    )
    assert criteria_count == 0


async def test_workspace_isolation_on_reviews(db_session: AsyncSession) -> None:
    workspace_a, case_a, reviewer, agent = await _create_workspace_case_users(
        db_session,
    )
    workspace_b, case_b = await _create_second_workspace_case(db_session, reviewer)
    review_a = await create_qa_review(db_session, case_a.id, reviewer.id, agent.id)
    review_b = await create_qa_review(db_session, case_b.id, reviewer.id, agent.id)

    workspace_a_reviews = (
        await db_session.scalars(
            select(CaseQaReview).where(
                CaseQaReview.workspace_id == workspace_a.id,
            )
        )
    ).all()
    workspace_b_reviews = (
        await db_session.scalars(
            select(CaseQaReview).where(
                CaseQaReview.workspace_id == workspace_b.id,
            )
        )
    ).all()

    assert {review.id for review in workspace_a_reviews} == {review_a.id}
    assert {review.id for review in workspace_b_reviews} == {review_b.id}
    assert review_a.workspace_id != review_b.workspace_id


async def test_invalid_criteria_score_raises(db_session: AsyncSession) -> None:
    _workspace, case, reviewer, agent = await _create_workspace_case_users(db_session)
    review = await create_qa_review(db_session, case.id, reviewer.id, agent.id)

    with pytest.raises(InvalidQaScoreError):
        await add_criteria_score(db_session, review.id, "tone", 101)
