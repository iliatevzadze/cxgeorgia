"""Agent workforce API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AgentShiftRead(BaseModel):
    """Public agent shift representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    user_id: UUID
    clock_in_at: datetime
    clock_out_at: datetime | None
    is_active: bool
    created_at: datetime


class AgentActiveShiftRead(BaseModel):
    """Current user's active shift response."""

    shift: AgentShiftRead | None


class AgentCaseMetricRead(BaseModel):
    """Public agent case metric representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    case_id: UUID
    user_id: UUID
    assigned_at: datetime | None
    first_response_at: datetime | None
    resolved_at: datetime | None
    messages_count: int
