"""Workspace saved Universal Case list view API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.workspace_deps import get_active_workspace_membership
from app.db.session import get_async_session
from app.models.case_list_view import CaseListView
from app.models.workspace_membership import WorkspaceMembership
from app.schemas.case_list_view import (
    CaseListViewCreate,
    CaseListViewDeleteRead,
    CaseListViewRead,
    CaseListViewUpdate,
)

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/case-list-views",
    tags=["case-list-views"],
)

DUPLICATE_VIEW_NAME_MESSAGE = "Saved view name already exists in this workspace"


def _envelope(data: dict | list) -> dict:
    return {"data": data, "meta": {}, "error": None}


async def _get_workspace_case_list_view_or_404(
    session: AsyncSession,
    workspace_id: UUID,
    view_id: UUID,
) -> CaseListView:
    view = await session.scalar(
        select(CaseListView).where(
            CaseListView.id == view_id,
            CaseListView.workspace_id == workspace_id,
        )
    )
    if view is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved view not found",
        )
    return view


async def _ensure_view_name_available(
    session: AsyncSession,
    workspace_id: UUID,
    name: str,
    *,
    exclude_view_id: UUID | None = None,
) -> None:
    query = select(CaseListView.id).where(
        CaseListView.workspace_id == workspace_id,
        CaseListView.name == name,
    )
    if exclude_view_id is not None:
        query = query.where(CaseListView.id != exclude_view_id)
    if await session.scalar(query):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=DUPLICATE_VIEW_NAME_MESSAGE,
        )


async def _unset_other_default_views(
    session: AsyncSession,
    workspace_id: UUID,
    *,
    exclude_view_id: UUID | None = None,
) -> None:
    query = (
        update(CaseListView)
        .where(
            CaseListView.workspace_id == workspace_id,
            CaseListView.is_default.is_(True),
        )
        .values(is_default=False)
    )
    if exclude_view_id is not None:
        query = query.where(CaseListView.id != exclude_view_id)
    await session.execute(query)


@router.get("")
async def list_workspace_case_list_views(
    workspace_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """List saved case list views in the workspace."""
    _ = membership
    result = await session.scalars(
        select(CaseListView)
        .where(CaseListView.workspace_id == workspace_id)
        .order_by(CaseListView.name.asc())
    )
    items = [
        CaseListViewRead.model_validate(item).model_dump(mode="json")
        for item in result.all()
    ]
    return _envelope(items)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workspace_case_list_view(
    body: CaseListViewCreate,
    workspace_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Create a saved case list view in the workspace."""
    await _ensure_view_name_available(session, workspace_id, body.name)

    is_default = body.is_default if body.is_default is not None else False
    if is_default:
        await _unset_other_default_views(session, workspace_id)

    view = CaseListView(
        workspace_id=workspace_id,
        created_by_user_id=membership.user_id,
        name=body.name,
        description=body.description,
        filters=body.filters,
        sort_by=body.sort_by.value if body.sort_by is not None else None,
        sort_order=body.sort_order.value if body.sort_order is not None else None,
        page_size=body.page_size,
        is_default=is_default,
    )
    session.add(view)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=DUPLICATE_VIEW_NAME_MESSAGE,
        ) from exc
    await session.refresh(view)
    return _envelope(CaseListViewRead.model_validate(view).model_dump(mode="json"))


@router.get("/{view_id}")
async def get_workspace_case_list_view(
    workspace_id: UUID,
    view_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Get a saved case list view by id in the workspace."""
    _ = membership
    view = await _get_workspace_case_list_view_or_404(session, workspace_id, view_id)
    return _envelope(CaseListViewRead.model_validate(view).model_dump(mode="json"))


@router.patch("/{view_id}")
async def update_workspace_case_list_view(
    body: CaseListViewUpdate,
    workspace_id: UUID,
    view_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Update a saved case list view in the workspace."""
    _ = membership
    view = await _get_workspace_case_list_view_or_404(session, workspace_id, view_id)

    if "name" in body.model_fields_set and body.name is not None:
        await _ensure_view_name_available(
            session,
            workspace_id,
            body.name,
            exclude_view_id=view_id,
        )
        view.name = body.name
    if "description" in body.model_fields_set:
        view.description = body.description
    if "filters" in body.model_fields_set and body.filters is not None:
        view.filters = body.filters
    if "sort_by" in body.model_fields_set:
        view.sort_by = body.sort_by.value if body.sort_by is not None else None
    if "sort_order" in body.model_fields_set:
        view.sort_order = (
            body.sort_order.value if body.sort_order is not None else None
        )
    if "page_size" in body.model_fields_set:
        view.page_size = body.page_size
    if "is_default" in body.model_fields_set and body.is_default is not None:
        if body.is_default:
            await _unset_other_default_views(
                session,
                workspace_id,
                exclude_view_id=view_id,
            )
        view.is_default = body.is_default

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=DUPLICATE_VIEW_NAME_MESSAGE,
        ) from exc
    await session.refresh(view)
    return _envelope(CaseListViewRead.model_validate(view).model_dump(mode="json"))


@router.delete("/{view_id}")
async def delete_workspace_case_list_view(
    workspace_id: UUID,
    view_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Delete a saved case list view from the workspace."""
    _ = membership
    view = await _get_workspace_case_list_view_or_404(session, workspace_id, view_id)
    await session.delete(view)
    await session.commit()
    return _envelope(
        CaseListViewDeleteRead(id=view_id, deleted=True).model_dump(mode="json")
    )
