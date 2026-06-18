"""Universal Case comment API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
