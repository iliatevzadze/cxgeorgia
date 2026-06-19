"""Saved case list view API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import CaseListSortBy, CaseListSortOrder

CASE_LIST_VIEW_PAGE_SIZES = frozenset({10, 25, 50, 100})


class CaseListViewCreate(BaseModel):
    """Create saved case list view request body."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    sort_by: CaseListSortBy | None = None
    sort_order: CaseListSortOrder | None = None
    page_size: int | None = None
    is_default: bool | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_required_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("Value must not be empty")
        return value

    @field_validator("description", mode="before")
    @classmethod
    def strip_optional_description(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        return value

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, value: int | None) -> int | None:
        if value is not None and value not in CASE_LIST_VIEW_PAGE_SIZES:
            raise ValueError(
                "page_size must be one of: 10, 25, 50, 100",
            )
        return value


class CaseListViewUpdate(BaseModel):
    """Update saved case list view request body."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    filters: dict[str, Any] | None = None
    sort_by: CaseListSortBy | None = None
    sort_order: CaseListSortOrder | None = None
    page_size: int | None = None
    is_default: bool | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_optional_name(cls, value: object) -> object:
        if value is None:
            raise ValueError("Value must not be null")
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("name")
    @classmethod
    def optional_name_not_empty(cls, value: str | None) -> str | None:
        if value is not None and not value:
            raise ValueError("Value must not be empty")
        return value

    @field_validator("description", mode="before")
    @classmethod
    def strip_optional_description(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        return value

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, value: int | None) -> int | None:
        if value is not None and value not in CASE_LIST_VIEW_PAGE_SIZES:
            raise ValueError(
                "page_size must be one of: 10, 25, 50, 100",
            )
        return value

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "CaseListViewUpdate":
        if not self.model_fields_set:
            raise ValueError(
                "At least one of name, description, filters, sort_by, "
                "sort_order, page_size or is_default must be provided",
            )
        return self


class CaseListViewRead(BaseModel):
    """Public saved case list view representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    created_by_user_id: UUID | None
    name: str
    description: str | None
    filters: dict[str, Any]
    sort_by: str | None
    sort_order: str | None
    page_size: int | None
    is_default: bool
    created_at: datetime
    updated_at: datetime


class CaseListViewDeleteRead(BaseModel):
    """Delete saved case list view response."""

    id: UUID
    deleted: bool
