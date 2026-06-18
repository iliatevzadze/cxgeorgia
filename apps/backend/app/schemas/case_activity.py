"""Universal Case activity API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CaseActivityType


class CaseActivityRead(BaseModel):
    """Public case activity representation."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    workspace_id: UUID
    case_id: UUID
    actor_user_id: UUID | None
    activity_type: CaseActivityType
    message: str | None
    metadata: dict[str, Any] = Field(validation_alias="activity_metadata")
    created_at: datetime
