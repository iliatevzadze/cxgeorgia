"""Workspace API dependencies."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_async_session
from app.models.enums import WorkspaceMemberStatus
from app.models.user import User
from app.models.workspace_membership import WorkspaceMembership

WORKSPACE_NOT_FOUND_MESSAGE = "Workspace not found"


async def get_active_workspace_membership(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> WorkspaceMembership:
    """Return the current user's active membership in a workspace, or 404."""
    membership = await session.scalar(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == current_user.id,
            WorkspaceMembership.status == WorkspaceMemberStatus.ACTIVE,
        )
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WORKSPACE_NOT_FOUND_MESSAGE,
        )
    return membership
