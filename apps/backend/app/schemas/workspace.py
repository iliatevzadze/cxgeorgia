"""Workspace API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import (
    WorkspaceMemberRole,
    WorkspaceMemberStatus,
    WorkspaceStatus,
)


class WorkspaceCreate(BaseModel):
    """Create workspace request body."""

    name: str = Field(min_length=2, max_length=120)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()


class WorkspaceRead(BaseModel):
    """Public workspace representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    status: WorkspaceStatus
    created_at: datetime
    updated_at: datetime


class WorkspaceMembershipRead(BaseModel):
    """Workspace membership representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: WorkspaceMemberRole
    status: WorkspaceMemberStatus
    created_at: datetime
    updated_at: datetime


class WorkspaceWithMembershipRead(BaseModel):
    """Workspace paired with the current user's membership."""

    workspace: WorkspaceRead
    membership: WorkspaceMembershipRead
