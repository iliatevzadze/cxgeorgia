"""Universal Case attachment API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CaseAttachmentCreate(BaseModel):
    """Create case attachment metadata request body."""

    model_config = ConfigDict(extra="forbid")

    file_name: str = Field(min_length=1, max_length=512)
    content_type: str | None = Field(default=None, max_length=255)
    size_bytes: int = Field(gt=0)
    storage_bucket: str = Field(min_length=1, max_length=255)
    storage_key: str = Field(min_length=1, max_length=1024)
    checksum_sha256: str | None = Field(default=None, max_length=64)

    @field_validator("file_name", "storage_bucket", "storage_key", mode="before")
    @classmethod
    def strip_required_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("file_name", "storage_bucket", "storage_key")
    @classmethod
    def required_text_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("Value must not be empty")
        return value

    @field_validator("content_type", mode="before")
    @classmethod
    def strip_optional_content_type(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        return value

    @field_validator("checksum_sha256", mode="before")
    @classmethod
    def strip_optional_checksum(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        return value

    @field_validator("checksum_sha256")
    @classmethod
    def checksum_length(cls, value: str | None) -> str | None:
        if value is not None and len(value) != 64:
            raise ValueError("checksum_sha256 must be 64 characters")
        return value


class CaseAttachmentRead(BaseModel):
    """Public case attachment metadata representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    case_id: UUID
    uploaded_by_user_id: UUID | None
    file_name: str
    content_type: str | None
    size_bytes: int
    storage_bucket: str
    storage_key: str
    checksum_sha256: str | None
    created_at: datetime


class CaseAttachmentDeleteRead(BaseModel):
    """Delete case attachment response."""

    id: UUID
    deleted: bool
