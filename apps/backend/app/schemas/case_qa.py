"""Case QA review API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import QaReviewStatus


class CaseQaReviewCreate(BaseModel):
    """Create case QA review request body."""

    model_config = ConfigDict(extra="forbid")

    reviewed_agent_user_id: UUID
    overall_comment: str | None = None

    @field_validator("overall_comment", mode="before")
    @classmethod
    def strip_optional_comment(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        return value


class CaseQaCriteriaScoreCreate(BaseModel):
    """Add criterion score to a QA review request body."""

    model_config = ConfigDict(extra="forbid")

    criterion_name: str = Field(min_length=1, max_length=128)
    score: int = Field(ge=0, le=100)
    comment: str | None = None

    @field_validator("criterion_name", mode="before")
    @classmethod
    def strip_criterion_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("criterion_name")
    @classmethod
    def criterion_name_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("Value must not be empty")
        return value

    @field_validator("comment", mode="before")
    @classmethod
    def strip_optional_comment(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        return value


class CaseQaCriteriaScoreRead(BaseModel):
    """Public case QA criteria score representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    qa_review_id: UUID
    criterion_name: str
    score: int
    comment: str | None


class CaseQaReviewRead(BaseModel):
    """Public case QA review representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    case_id: UUID
    reviewed_by_user_id: UUID | None
    reviewed_agent_user_id: UUID | None
    score: int
    status: QaReviewStatus
    overall_comment: str | None
    created_at: datetime
    updated_at: datetime
    criteria_scores: list[CaseQaCriteriaScoreRead] = Field(default_factory=list)


class CaseQaReviewStatusUpdateRead(BaseModel):
    """QA review status update response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: QaReviewStatus
    score: int
    updated_at: datetime
