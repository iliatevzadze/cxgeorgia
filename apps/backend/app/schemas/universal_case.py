"""Universal Case API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import CasePriority, CaseSource, CaseStatus


class UniversalCaseCreate(BaseModel):
    """Create universal case request body."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: CaseStatus = CaseStatus.OPEN
    priority: CasePriority = CasePriority.NORMAL
    source: CaseSource = CaseSource.MANUAL
    customer_name: str | None = Field(default=None, max_length=255)
    customer_email: str | None = Field(default=None, max_length=320)
    external_reference: str | None = Field(default=None, max_length=255)
    assigned_to_user_id: UUID | None = None

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class UniversalCaseRead(BaseModel):
    """Public universal case representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    title: str
    description: str | None
    status: CaseStatus
    priority: CasePriority
    source: CaseSource
    customer_name: str | None
    customer_email: str | None
    external_reference: str | None
    created_by_user_id: UUID | None
    assigned_to_user_id: UUID | None
    created_at: datetime
    updated_at: datetime
