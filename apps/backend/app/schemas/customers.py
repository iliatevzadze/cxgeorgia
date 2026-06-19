"""Customer record API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import CustomerStatus


class CustomerCreate(BaseModel):
    """Create customer request body."""

    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=64)
    external_id: str | None = Field(default=None, max_length=255)
    locale: str | None = Field(default=None, max_length=32)
    notes: str | None = None
    status: CustomerStatus | None = None

    @field_validator("display_name", mode="before")
    @classmethod
    def strip_required_display_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("display_name")
    @classmethod
    def display_name_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("Value must not be empty")
        return value

    @field_validator("email", "phone", "external_id", "locale", mode="before")
    @classmethod
    def strip_optional_text(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        return value


class CustomerUpdate(BaseModel):
    """Update customer request body."""

    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=64)
    external_id: str | None = Field(default=None, max_length=255)
    locale: str | None = Field(default=None, max_length=32)
    notes: str | None = None
    status: CustomerStatus | None = None

    @field_validator("display_name", mode="before")
    @classmethod
    def strip_optional_display_name(cls, value: object) -> object:
        if value is None:
            raise ValueError("Value must not be null")
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("display_name")
    @classmethod
    def optional_display_name_not_empty(cls, value: str | None) -> str | None:
        if value is not None and not value:
            raise ValueError("Value must not be empty")
        return value

    @field_validator("email", "phone", "external_id", "locale", mode="before")
    @classmethod
    def strip_optional_text(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        return value

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "CustomerUpdate":
        if not self.model_fields_set:
            raise ValueError(
                "At least one of display_name, email, phone, external_id, "
                "locale, notes or status must be provided",
            )
        return self


class CustomerRead(BaseModel):
    """Public customer record representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    display_name: str
    email: str | None
    phone: str | None
    external_id: str | None
    locale: str | None
    notes: str | None
    status: CustomerStatus
    created_at: datetime
    updated_at: datetime


class CustomerDeleteRead(BaseModel):
    """Delete customer response."""

    id: UUID
    deleted: bool
