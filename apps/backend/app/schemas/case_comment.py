"""Universal Case comment API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CaseCommentCreate(BaseModel):
    """Create case comment request body."""

    model_config = ConfigDict(extra="forbid")

    body: str = Field(min_length=1)
    is_internal: bool = True

    @field_validator("body", mode="before")
    @classmethod
    def strip_body(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("Body must not be empty")
        return value

    @field_validator("is_internal", mode="before")
    @classmethod
    def reject_null_is_internal(cls, value: object) -> object:
        if value is None:
            raise ValueError("is_internal must not be null")
        return value


class CaseCommentUpdate(BaseModel):
    """Update case comment request body."""

    model_config = ConfigDict(extra="forbid")

    body: str | None = Field(default=None, min_length=1)
    is_internal: bool | None = None

    @field_validator("body", mode="before")
    @classmethod
    def strip_body(cls, value: object) -> object:
        if value is None:
            raise ValueError("Body must not be null")
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, value: str | None) -> str | None:
        if value is not None and not value:
            raise ValueError("Body must not be empty")
        return value

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "CaseCommentUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one of body or is_internal must be provided")
        if "body" in self.model_fields_set and self.body is None:
            raise ValueError("Body must not be null")
        if "is_internal" in self.model_fields_set and self.is_internal is None:
            raise ValueError("is_internal must not be null")
        return self


class CaseCommentRead(BaseModel):
    """Public case comment representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    case_id: UUID
    author_user_id: UUID | None
    body: str
    is_internal: bool
    created_at: datetime
    updated_at: datetime


class CaseCommentDeleteRead(BaseModel):
    """Delete case comment response."""

    id: UUID
    deleted: bool
