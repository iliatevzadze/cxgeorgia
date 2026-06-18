"""Universal Case API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.case_tags import get_workspace_case_tag_or_404
from app.api.workspace_deps import get_active_workspace_membership
from app.db.session import get_async_session
from app.models.case_activity import CaseActivity
from app.models.case_comment import CaseComment
from app.models.case_tag import CaseTag, UniversalCaseTag
from app.models.enums import WorkspaceMemberStatus
from app.models.universal_case import UniversalCase
from app.models.workspace_membership import WorkspaceMembership
from app.schemas.case_activity import CaseActivityRead
from app.schemas.case_comment import (
    CaseCommentCreate,
    CaseCommentDeleteRead,
    CaseCommentRead,
    CaseCommentUpdate,
)
from app.schemas.case_tag import CaseTagDetachRead, CaseTagRead
from app.schemas.universal_case import (
    UniversalCaseCreate,
    UniversalCaseDeleteRead,
    UniversalCaseRead,
    UniversalCaseUpdate,
)
from app.services.case_activity import (
    record_case_created_activity,
    record_case_patch_activities,
    record_comment_created_activity,
    record_comment_deleted_activity,
    record_comment_edited_activity,
    record_tag_attached_activity,
    record_tag_detached_activity,
    snapshot_case,
)

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/cases",
    tags=["universal-cases"],
)


def _envelope(data: dict | list) -> dict:
    return {"data": data, "meta": {}, "error": None}


async def _require_active_workspace_assignee(
    session: AsyncSession,
    workspace_id: UUID,
    user_id: UUID,
) -> None:
    membership = await session.scalar(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user_id,
            WorkspaceMembership.status == WorkspaceMemberStatus.ACTIVE,
        )
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Assignee must be an active member of this workspace",
        )


async def _get_workspace_case_or_404(
    session: AsyncSession,
    workspace_id: UUID,
    case_id: UUID,
) -> UniversalCase:
    case = await session.scalar(
        select(UniversalCase).where(
            UniversalCase.id == case_id,
            UniversalCase.workspace_id == workspace_id,
        )
    )
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    return case


async def _get_workspace_case_comment_or_404(
    session: AsyncSession,
    workspace_id: UUID,
    case_id: UUID,
    comment_id: UUID,
) -> CaseComment:
    comment = await session.scalar(
        select(CaseComment).where(
            CaseComment.id == comment_id,
            CaseComment.workspace_id == workspace_id,
            CaseComment.case_id == case_id,
        )
    )
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    return comment


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_case(
    body: UniversalCaseCreate,
    workspace_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Create a universal case in the workspace."""
    case = UniversalCase(
        workspace_id=workspace_id,
        title=body.title,
        description=body.description,
        status=body.status,
        priority=body.priority,
        source=body.source,
        customer_name=body.customer_name,
        customer_email=body.customer_email,
        external_reference=body.external_reference,
        created_by_user_id=membership.user_id,
        assigned_to_user_id=body.assigned_to_user_id,
    )
    session.add(case)
    await session.flush()
    record_case_created_activity(
        session,
        workspace_id=workspace_id,
        case=case,
        actor_user_id=membership.user_id,
    )
    await session.commit()
    await session.refresh(case)
    return _envelope(UniversalCaseRead.model_validate(case).model_dump(mode="json"))


@router.get("")
async def list_cases(
    workspace_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """List universal cases in the workspace, newest first."""
    _ = membership
    result = await session.scalars(
        select(UniversalCase)
        .where(UniversalCase.workspace_id == workspace_id)
        .order_by(UniversalCase.created_at.desc())
    )
    items = [
        UniversalCaseRead.model_validate(item).model_dump(mode="json")
        for item in result.all()
    ]
    return _envelope(items)


@router.get("/{case_id}")
async def get_case(
    workspace_id: UUID,
    case_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Return a universal case by id within the workspace."""
    _ = membership
    case = await session.scalar(
        select(UniversalCase).where(
            UniversalCase.id == case_id,
            UniversalCase.workspace_id == workspace_id,
        )
    )
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    return _envelope(UniversalCaseRead.model_validate(case).model_dump(mode="json"))


@router.patch("/{case_id}")
async def update_case(
    body: UniversalCaseUpdate,
    workspace_id: UUID,
    case_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Update universal case fields allowed by PATCH."""
    case = await session.scalar(
        select(UniversalCase).where(
            UniversalCase.id == case_id,
            UniversalCase.workspace_id == workspace_id,
        )
    )
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    before = snapshot_case(case)

    if "title" in body.model_fields_set and body.title is not None:
        case.title = body.title
    if "description" in body.model_fields_set:
        case.description = body.description
    if body.status is not None:
        case.status = body.status
    if body.priority is not None:
        case.priority = body.priority
    if body.source is not None:
        case.source = body.source
    if "customer_name" in body.model_fields_set:
        case.customer_name = body.customer_name
    if "customer_email" in body.model_fields_set:
        case.customer_email = body.customer_email
    if "external_reference" in body.model_fields_set:
        case.external_reference = body.external_reference
    if "assigned_to_user_id" in body.model_fields_set:
        if body.assigned_to_user_id is not None:
            await _require_active_workspace_assignee(
                session,
                workspace_id,
                body.assigned_to_user_id,
            )
        case.assigned_to_user_id = body.assigned_to_user_id

    record_case_patch_activities(
        session,
        workspace_id=workspace_id,
        case=case,
        actor_user_id=membership.user_id,
        before=before,
        body=body,
    )
    await session.commit()
    await session.refresh(case)
    return _envelope(UniversalCaseRead.model_validate(case).model_dump(mode="json"))


@router.delete("/{case_id}")
async def delete_case(
    workspace_id: UUID,
    case_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Delete a universal case from the workspace."""
    _ = membership
    case = await session.scalar(
        select(UniversalCase).where(
            UniversalCase.id == case_id,
            UniversalCase.workspace_id == workspace_id,
        )
    )
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    await session.delete(case)
    await session.commit()
    return _envelope(
        UniversalCaseDeleteRead(id=case_id, deleted=True).model_dump(mode="json")
    )


@router.post("/{case_id}/comments", status_code=status.HTTP_201_CREATED)
async def create_case_comment(
    body: CaseCommentCreate,
    workspace_id: UUID,
    case_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Create a comment on a universal case in the workspace."""
    await _get_workspace_case_or_404(session, workspace_id, case_id)

    comment = CaseComment(
        workspace_id=workspace_id,
        case_id=case_id,
        author_user_id=membership.user_id,
        body=body.body,
        is_internal=body.is_internal,
    )
    session.add(comment)
    await session.flush()
    record_comment_created_activity(
        session,
        workspace_id=workspace_id,
        case_id=case_id,
        actor_user_id=membership.user_id,
        comment_id=comment.id,
        is_internal=comment.is_internal,
    )
    await session.commit()
    await session.refresh(comment)
    return _envelope(CaseCommentRead.model_validate(comment).model_dump(mode="json"))


@router.get("/{case_id}/comments")
async def list_case_comments(
    workspace_id: UUID,
    case_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """List comments for a universal case, oldest first."""
    _ = membership
    await _get_workspace_case_or_404(session, workspace_id, case_id)

    result = await session.scalars(
        select(CaseComment)
        .where(
            CaseComment.workspace_id == workspace_id,
            CaseComment.case_id == case_id,
        )
        .order_by(CaseComment.created_at.asc())
    )
    items = [
        CaseCommentRead.model_validate(item).model_dump(mode="json")
        for item in result.all()
    ]
    return _envelope(items)


@router.get("/{case_id}/activities")
async def list_case_activities(
    workspace_id: UUID,
    case_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """List activity timeline records for a universal case, newest first."""
    _ = membership
    await _get_workspace_case_or_404(session, workspace_id, case_id)

    result = await session.scalars(
        select(CaseActivity)
        .where(
            CaseActivity.workspace_id == workspace_id,
            CaseActivity.case_id == case_id,
        )
        .order_by(CaseActivity.created_at.desc())
    )
    items = [
        CaseActivityRead.model_validate(item).model_dump(mode="json")
        for item in result.all()
    ]
    return _envelope(items)


@router.patch("/{case_id}/comments/{comment_id}")
async def update_case_comment(
    body: CaseCommentUpdate,
    workspace_id: UUID,
    case_id: UUID,
    comment_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Update a comment on a universal case in the workspace."""
    await _get_workspace_case_or_404(session, workspace_id, case_id)
    comment = await _get_workspace_case_comment_or_404(
        session,
        workspace_id,
        case_id,
        comment_id,
    )

    changed_fields: list[str] = []

    if "body" in body.model_fields_set and body.body != comment.body:
        comment.body = body.body
        changed_fields.append("body")

    if (
        "is_internal" in body.model_fields_set
        and body.is_internal != comment.is_internal
    ):
        comment.is_internal = body.is_internal
        changed_fields.append("is_internal")

    if changed_fields:
        record_comment_edited_activity(
            session,
            workspace_id=workspace_id,
            case_id=case_id,
            actor_user_id=membership.user_id,
            comment_id=comment.id,
            changed_fields=changed_fields,
        )
        await session.commit()
        await session.refresh(comment)

    return _envelope(CaseCommentRead.model_validate(comment).model_dump(mode="json"))


@router.delete("/{case_id}/comments/{comment_id}")
async def delete_case_comment(
    workspace_id: UUID,
    case_id: UUID,
    comment_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Delete a comment from a universal case in the workspace."""
    _ = membership
    await _get_workspace_case_or_404(session, workspace_id, case_id)
    comment = await _get_workspace_case_comment_or_404(
        session,
        workspace_id,
        case_id,
        comment_id,
    )
    comment_id_value = comment.id
    is_internal = comment.is_internal

    await session.delete(comment)
    record_comment_deleted_activity(
        session,
        workspace_id=workspace_id,
        case_id=case_id,
        actor_user_id=membership.user_id,
        comment_id=comment_id_value,
        is_internal=is_internal,
    )
    await session.commit()
    return _envelope(
        CaseCommentDeleteRead(id=comment_id, deleted=True).model_dump(mode="json")
    )


@router.get("/{case_id}/tags")
async def list_case_tags(
    workspace_id: UUID,
    case_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """List tags attached to a universal case."""
    _ = membership
    await _get_workspace_case_or_404(session, workspace_id, case_id)

    result = await session.scalars(
        select(CaseTag)
        .join(UniversalCaseTag, UniversalCaseTag.tag_id == CaseTag.id)
        .where(
            UniversalCaseTag.case_id == case_id,
            CaseTag.workspace_id == workspace_id,
        )
        .order_by(CaseTag.name.asc())
    )
    items = [
        CaseTagRead.model_validate(item).model_dump(mode="json")
        for item in result.all()
    ]
    return _envelope(items)


@router.post("/{case_id}/tags/{tag_id}")
async def attach_case_tag(
    workspace_id: UUID,
    case_id: UUID,
    tag_id: UUID,
    response: Response,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Attach a workspace tag to a universal case."""
    await _get_workspace_case_or_404(session, workspace_id, case_id)
    tag = await get_workspace_case_tag_or_404(session, workspace_id, tag_id)

    existing = await session.scalar(
        select(UniversalCaseTag).where(
            UniversalCaseTag.case_id == case_id,
            UniversalCaseTag.tag_id == tag_id,
        )
    )
    if existing is not None:
        response.status_code = status.HTTP_200_OK
        return _envelope(CaseTagRead.model_validate(tag).model_dump(mode="json"))

    session.add(UniversalCaseTag(case_id=case_id, tag_id=tag_id))
    record_tag_attached_activity(
        session,
        workspace_id=workspace_id,
        case_id=case_id,
        actor_user_id=membership.user_id,
        tag_id=tag.id,
        tag_name=tag.name,
        tag_slug=tag.slug,
    )
    await session.commit()
    response.status_code = status.HTTP_201_CREATED
    return _envelope(CaseTagRead.model_validate(tag).model_dump(mode="json"))


@router.delete("/{case_id}/tags/{tag_id}")
async def detach_case_tag(
    workspace_id: UUID,
    case_id: UUID,
    tag_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Detach a workspace tag from a universal case."""
    await _get_workspace_case_or_404(session, workspace_id, case_id)
    tag = await get_workspace_case_tag_or_404(session, workspace_id, tag_id)

    join_row = await session.scalar(
        select(UniversalCaseTag).where(
            UniversalCaseTag.case_id == case_id,
            UniversalCaseTag.tag_id == tag_id,
        )
    )
    if join_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not attached to case",
        )

    await session.delete(join_row)
    record_tag_detached_activity(
        session,
        workspace_id=workspace_id,
        case_id=case_id,
        actor_user_id=membership.user_id,
        tag_id=tag.id,
        tag_name=tag.name,
        tag_slug=tag.slug,
    )
    await session.commit()
    return _envelope(
        CaseTagDetachRead(tag_id=tag_id, detached=True).model_dump(mode="json")
    )
