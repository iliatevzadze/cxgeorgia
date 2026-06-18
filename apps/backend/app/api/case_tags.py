"""Workspace Universal Case tag API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.workspace_deps import get_active_workspace_membership
from app.db.session import get_async_session
from app.models.case_tag import CaseTag
from app.models.workspace_membership import WorkspaceMembership
from app.schemas.case_tag import (
    CaseTagCreate,
    CaseTagDeleteRead,
    CaseTagRead,
    CaseTagUpdate,
)

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/case-tags",
    tags=["case-tags"],
)

DUPLICATE_TAG_SLUG_MESSAGE = "Tag slug already exists in this workspace"


def _envelope(data: dict | list) -> dict:
    return {"data": data, "meta": {}, "error": None}


async def get_workspace_case_tag_or_404(
    session: AsyncSession,
    workspace_id: UUID,
    tag_id: UUID,
) -> CaseTag:
    tag = await session.scalar(
        select(CaseTag).where(
            CaseTag.id == tag_id,
            CaseTag.workspace_id == workspace_id,
        )
    )
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
    return tag


async def _ensure_tag_slug_available(
    session: AsyncSession,
    workspace_id: UUID,
    slug: str,
    *,
    exclude_tag_id: UUID | None = None,
) -> None:
    query = select(CaseTag.id).where(
        CaseTag.workspace_id == workspace_id,
        CaseTag.slug == slug,
    )
    if exclude_tag_id is not None:
        query = query.where(CaseTag.id != exclude_tag_id)
    if await session.scalar(query):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=DUPLICATE_TAG_SLUG_MESSAGE,
        )


@router.get("")
async def list_workspace_case_tags(
    workspace_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """List workspace case tags."""
    _ = membership
    result = await session.scalars(
        select(CaseTag)
        .where(CaseTag.workspace_id == workspace_id)
        .order_by(CaseTag.name.asc())
    )
    items = [
        CaseTagRead.model_validate(item).model_dump(mode="json")
        for item in result.all()
    ]
    return _envelope(items)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workspace_case_tag(
    body: CaseTagCreate,
    workspace_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Create a workspace case tag."""
    _ = membership
    await _ensure_tag_slug_available(session, workspace_id, body.slug)

    tag = CaseTag(
        workspace_id=workspace_id,
        name=body.name,
        slug=body.slug,
        color=body.color,
    )
    session.add(tag)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=DUPLICATE_TAG_SLUG_MESSAGE,
        ) from exc
    await session.refresh(tag)
    return _envelope(CaseTagRead.model_validate(tag).model_dump(mode="json"))


@router.patch("/{tag_id}")
async def update_workspace_case_tag(
    body: CaseTagUpdate,
    workspace_id: UUID,
    tag_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Update a workspace case tag."""
    _ = membership
    tag = await get_workspace_case_tag_or_404(session, workspace_id, tag_id)

    if "name" in body.model_fields_set:
        tag.name = body.name
    if "color" in body.model_fields_set:
        tag.color = body.color
    if "slug" in body.model_fields_set and body.slug != tag.slug:
        await _ensure_tag_slug_available(
            session,
            workspace_id,
            body.slug,
            exclude_tag_id=tag.id,
        )
        tag.slug = body.slug

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=DUPLICATE_TAG_SLUG_MESSAGE,
        ) from exc
    await session.refresh(tag)
    return _envelope(CaseTagRead.model_validate(tag).model_dump(mode="json"))


@router.delete("/{tag_id}")
async def delete_workspace_case_tag(
    workspace_id: UUID,
    tag_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Delete a workspace case tag."""
    _ = membership
    tag = await get_workspace_case_tag_or_404(session, workspace_id, tag_id)
    await session.delete(tag)
    await session.commit()
    return _envelope(
        CaseTagDeleteRead(id=tag_id, deleted=True).model_dump(mode="json")
    )
