"""Workspace bootstrap API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.workspace_deps import get_active_workspace_membership
from app.core.slugify import slugify_workspace_name
from app.db.session import get_async_session
from app.models.enums import (
    WorkspaceMemberRole,
    WorkspaceMemberStatus,
    WorkspaceStatus,
)
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_membership import WorkspaceMembership
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceMembershipRead,
    WorkspaceRead,
    WorkspaceWithMembershipRead,
)

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])


def _envelope(data: dict | list) -> dict:
    return {"data": data, "meta": {}, "error": None}


async def _generate_unique_slug(name: str, session: AsyncSession) -> str:
    base_slug = slugify_workspace_name(name)
    slug = base_slug
    suffix = 2
    while await session.scalar(select(Workspace.id).where(Workspace.slug == slug)):
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    return slug


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    body: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Create a workspace and assign the current user as owner."""
    slug = await _generate_unique_slug(body.name, session)
    workspace = Workspace(
        name=body.name,
        slug=slug,
        status=WorkspaceStatus.ACTIVE,
    )
    membership = WorkspaceMembership(
        workspace=workspace,
        user_id=current_user.id,
        role=WorkspaceMemberRole.OWNER,
        status=WorkspaceMemberStatus.ACTIVE,
    )
    session.add(workspace)
    session.add(membership)
    await session.commit()
    await session.refresh(workspace)
    await session.refresh(membership)

    payload = WorkspaceWithMembershipRead(
        workspace=WorkspaceRead.model_validate(workspace),
        membership=WorkspaceMembershipRead.model_validate(membership),
    )
    return _envelope(payload.model_dump(mode="json"))


@router.get("")
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """List workspaces where the current user has an active membership."""
    result = await session.execute(
        select(Workspace, WorkspaceMembership)
        .join(
            WorkspaceMembership,
            WorkspaceMembership.workspace_id == Workspace.id,
        )
        .where(
            WorkspaceMembership.user_id == current_user.id,
            WorkspaceMembership.status == WorkspaceMemberStatus.ACTIVE,
            Workspace.status == WorkspaceStatus.ACTIVE,
        )
        .order_by(Workspace.created_at.asc())
    )
    items = [
        WorkspaceWithMembershipRead(
            workspace=WorkspaceRead.model_validate(workspace),
            membership=WorkspaceMembershipRead.model_validate(membership),
        ).model_dump(mode="json")
        for workspace, membership in result.all()
    ]
    return _envelope(items)


@router.get("/{workspace_id}")
async def get_workspace(
    workspace_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Return workspace detail for an active member."""
    workspace = await session.get(Workspace, workspace_id)
    if workspace is None or workspace.status != WorkspaceStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    _ = membership
    return _envelope(WorkspaceRead.model_validate(workspace).model_dump(mode="json"))


@router.get("/{workspace_id}/memberships")
async def list_workspace_memberships(
    workspace_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """List active memberships for a workspace."""
    _ = membership
    result = await session.scalars(
        select(WorkspaceMembership)
        .where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.status == WorkspaceMemberStatus.ACTIVE,
        )
        .order_by(WorkspaceMembership.created_at.asc())
    )
    items = [
        WorkspaceMembershipRead.model_validate(item).model_dump(mode="json")
        for item in result.all()
    ]
    return _envelope(items)
