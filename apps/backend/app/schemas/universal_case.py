"""Universal Case API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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


class UniversalCaseUpdate(BaseModel):
    """Update universal case title, description, status and/or priority."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    status: CaseStatus | None = None
    priority: CasePriority | None = None

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, value: str | None) -> str | None:
        if value is not None and not value:
            raise ValueError("Title must not be empty")
        return value

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "UniversalCaseUpdate":
        if not self.model_fields_set:
            raise ValueError(
                "At least one of title, description, status or priority "
                "must be provided"
            )
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("Title must not be null")
        return self


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
