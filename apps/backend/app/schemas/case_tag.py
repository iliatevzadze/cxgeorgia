"""Universal Case tag API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CaseTagCreate(BaseModel):
    """Create workspace case tag request body."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=100)
    color: str | None = Field(default=None, max_length=32)

    @field_validator("name", "slug", mode="before")
    @classmethod
    def strip_required_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("name", "slug")
    @classmethod
    def required_text_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("Value must not be empty")
        return value

    @field_validator("color", mode="before")
    @classmethod
    def strip_optional_color(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        return value


class CaseTagUpdate(BaseModel):
    """Update workspace case tag request body."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = Field(default=None, max_length=32)

    @field_validator("name", "slug", mode="before")
    @classmethod
    def strip_optional_text(cls, value: object) -> object:
        if value is None:
            raise ValueError("Value must not be null")
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("name", "slug")
    @classmethod
    def optional_text_not_empty(cls, value: str | None) -> str | None:
        if value is not None and not value:
            raise ValueError("Value must not be empty")
        return value

    @field_validator("color", mode="before")
    @classmethod
    def strip_optional_color(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        return value

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "CaseTagUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one of name, slug or color must be provided")
        if "color" in self.model_fields_set and self.color is None:
            return self
        return self


class CaseTagRead(BaseModel):
    """Public workspace case tag representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    slug: str
    color: str | None
    created_at: datetime
    updated_at: datetime


class CaseTagDeleteRead(BaseModel):
    """Delete workspace case tag response."""

    id: UUID
    deleted: bool


class CaseTagDetachRead(BaseModel):
    """Detach case tag response."""

    tag_id: UUID
    detached: bool
