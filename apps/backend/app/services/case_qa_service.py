"""Case QA review helpers."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_qa_criteria_score import CaseQaCriteriaScore
from app.models.case_qa_review import CaseQaReview
from app.models.enums import QaReviewStatus
from app.models.universal_case import UniversalCase


class CaseNotFoundError(Exception):
    """Raised when a Universal Case cannot be found."""


class QaReviewNotFoundError(Exception):
    """Raised when a QA review cannot be found."""


class InvalidQaScoreError(Exception):
    """Raised when a QA score is outside the allowed range."""


class InvalidQaReviewStatusError(Exception):
    """Raised when a QA review status transition is not allowed."""


def _validate_score(score: int) -> None:
    if score < 0 or score > 100:
        raise InvalidQaScoreError("Score must be between 0 and 100")


async def create_qa_review(
    session: AsyncSession,
    case_id: UUID,
    reviewer_id: UUID,
    agent_id: UUID,
) -> CaseQaReview:
    """Create a pending QA review for a case."""
    case = await session.get(UniversalCase, case_id)
    if case is None:
        raise CaseNotFoundError("Case not found")

    review = CaseQaReview(
        workspace_id=case.workspace_id,
        case_id=case_id,
        reviewed_by_user_id=reviewer_id,
        reviewed_agent_user_id=agent_id,
        score=0,
        status=QaReviewStatus.PENDING,
    )
    session.add(review)
    await session.flush()
    return review


async def add_criteria_score(
    session: AsyncSession,
    review_id: UUID,
    criterion: str,
    score: int,
    comment: str | None = None,
) -> CaseQaCriteriaScore:
    """Add a criterion score and recalculate the review final score."""
    _validate_score(score)
    review = await session.get(CaseQaReview, review_id)
    if review is None:
        raise QaReviewNotFoundError("QA review not found")

    criteria_score = CaseQaCriteriaScore(
        qa_review_id=review_id,
        criterion_name=criterion,
        score=score,
        comment=comment,
    )
    session.add(criteria_score)
    await session.flush()
    await calculate_final_score(session, review_id)
    return criteria_score


async def calculate_final_score(
    session: AsyncSession,
    review_id: UUID,
) -> int:
    """Set review score to the average of its criterion scores."""
    review = await session.get(CaseQaReview, review_id)
    if review is None:
        raise QaReviewNotFoundError("QA review not found")

    average = await session.scalar(
        select(func.avg(CaseQaCriteriaScore.score)).where(
            CaseQaCriteriaScore.qa_review_id == review_id,
        )
    )
    if average is None:
        review.score = 0
    else:
        review.score = round(float(average))
    await session.flush()
    return review.score


async def approve_review(
    session: AsyncSession,
    review_id: UUID,
) -> CaseQaReview:
    """Approve a pending QA review."""
    review = await session.get(CaseQaReview, review_id)
    if review is None:
        raise QaReviewNotFoundError("QA review not found")
    if review.status != QaReviewStatus.PENDING:
        raise InvalidQaReviewStatusError("Only pending reviews can be approved")

    review.status = QaReviewStatus.APPROVED
    await session.flush()
    return review


async def reject_review(
    session: AsyncSession,
    review_id: UUID,
) -> CaseQaReview:
    """Reject a pending QA review."""
    review = await session.get(CaseQaReview, review_id)
    if review is None:
        raise QaReviewNotFoundError("QA review not found")
    if review.status != QaReviewStatus.PENDING:
        raise InvalidQaReviewStatusError("Only pending reviews can be rejected")

    review.status = QaReviewStatus.REJECTED
    await session.flush()
    return review
