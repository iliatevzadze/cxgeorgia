"""Case QA review API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.universal_cases import (
    _get_workspace_case_or_404,
    _require_active_workspace_assignee,
)
from app.api.workspace_deps import get_active_workspace_membership
from app.db.session import get_async_session
from app.models.user import User
from app.models.workspace_membership import WorkspaceMembership
from app.schemas.case_qa import (
    CaseQaCriteriaScoreCreate,
    CaseQaReviewCreate,
    CaseQaReviewRead,
)
from app.services.case_qa_service import (
    InvalidQaReviewStatusError,
    InvalidQaScoreError,
    add_criteria_score,
    approve_review,
    create_qa_review,
    get_qa_review_for_case,
    list_qa_reviews_for_case,
    reject_review,
)

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/cases/{case_id}/qa-reviews",
    tags=["case-qa"],
)


def _envelope(data: dict | list) -> dict:
    return {"data": data, "meta": {}, "error": None}


def _review_payload(review) -> dict:
    return CaseQaReviewRead.model_validate(review).model_dump(mode="json")


async def _get_workspace_case_qa_review_or_404(
    session: AsyncSession,
    workspace_id: UUID,
    case_id: UUID,
    review_id: UUID,
):
    review = await get_qa_review_for_case(
        session,
        workspace_id,
        case_id,
        review_id,
    )
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QA review not found",
        )
    return review


@router.get("")
async def list_case_qa_reviews(
    workspace_id: UUID,
    case_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """List QA reviews for a case."""
    _ = membership
    await _get_workspace_case_or_404(session, workspace_id, case_id)
    reviews = await list_qa_reviews_for_case(session, workspace_id, case_id)
    items = [_review_payload(review) for review in reviews]
    return _envelope(items)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_case_qa_review(
    body: CaseQaReviewCreate,
    workspace_id: UUID,
    case_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Create a QA review for a case."""
    _ = membership
    await _get_workspace_case_or_404(session, workspace_id, case_id)
    await _require_active_workspace_assignee(
        session,
        workspace_id,
        body.reviewed_agent_user_id,
    )

    review = await create_qa_review(
        session,
        case_id,
        current_user.id,
        body.reviewed_agent_user_id,
        overall_comment=body.overall_comment,
    )
    await session.commit()
    review = await get_qa_review_for_case(
        session,
        workspace_id,
        case_id,
        review.id,
    )
    assert review is not None
    return _envelope(_review_payload(review))


@router.post("/{review_id}/criteria", status_code=status.HTTP_201_CREATED)
async def add_case_qa_criteria_score(
    body: CaseQaCriteriaScoreCreate,
    workspace_id: UUID,
    case_id: UUID,
    review_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Add a criterion score to a QA review."""
    _ = membership
    await _get_workspace_case_or_404(session, workspace_id, case_id)
    await _get_workspace_case_qa_review_or_404(
        session,
        workspace_id,
        case_id,
        review_id,
    )

    try:
        await add_criteria_score(
            session,
            review_id,
            body.criterion_name,
            body.score,
            comment=body.comment,
        )
        await session.commit()
    except InvalidQaScoreError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    review = await get_qa_review_for_case(
        session,
        workspace_id,
        case_id,
        review_id,
    )
    assert review is not None
    return _envelope(_review_payload(review))


@router.post("/{review_id}/approve")
async def approve_case_qa_review(
    workspace_id: UUID,
    case_id: UUID,
    review_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Approve a pending QA review."""
    _ = membership
    await _get_workspace_case_or_404(session, workspace_id, case_id)
    await _get_workspace_case_qa_review_or_404(
        session,
        workspace_id,
        case_id,
        review_id,
    )

    try:
        await approve_review(session, review_id)
        await session.commit()
    except InvalidQaReviewStatusError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    review = await get_qa_review_for_case(
        session,
        workspace_id,
        case_id,
        review_id,
    )
    assert review is not None
    return _envelope(_review_payload(review))


@router.post("/{review_id}/reject")
async def reject_case_qa_review(
    workspace_id: UUID,
    case_id: UUID,
    review_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Reject a pending QA review."""
    _ = membership
    await _get_workspace_case_or_404(session, workspace_id, case_id)
    await _get_workspace_case_qa_review_or_404(
        session,
        workspace_id,
        case_id,
        review_id,
    )

    try:
        await reject_review(session, review_id)
        await session.commit()
    except InvalidQaReviewStatusError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    review = await get_qa_review_for_case(
        session,
        workspace_id,
        case_id,
        review_id,
    )
    assert review is not None
    return _envelope(_review_payload(review))
