"""Universal Case API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.workspace_deps import get_active_workspace_membership
from app.db.session import get_async_session
from app.models.enums import WorkspaceMemberStatus
from app.models.universal_case import UniversalCase
from app.models.workspace_membership import WorkspaceMembership
from app.schemas.universal_case import (
    UniversalCaseCreate,
    UniversalCaseDeleteRead,
    UniversalCaseRead,
    UniversalCaseUpdate,
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
