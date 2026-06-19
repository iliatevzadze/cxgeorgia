"""Operations dashboard API schemas."""

from pydantic import BaseModel


class OperationsCasesSummary(BaseModel):
    """Case volume summary for a workspace."""

    total_cases: int
    open_cases: int
    pending_cases: int
    resolved_cases: int


class OperationsSlaSummary(BaseModel):
    """SLA status distribution for a workspace."""

    on_track: int
    at_risk: int
    breached: int


class OperationsAgentsSummary(BaseModel):
    """Agent workload summary for a workspace."""

    active_shifts: int
    total_agent_case_metrics: int
    total_agent_messages: int


class OperationsQaSummary(BaseModel):
    """QA review summary for a workspace."""

    total_reviews: int
    pending_reviews: int
    approved_reviews: int
    rejected_reviews: int
    average_score: float


class OperationsDashboardRead(BaseModel):
    """Aggregated operations dashboard for a workspace."""

    cases: OperationsCasesSummary
    sla: OperationsSlaSummary
    agents: OperationsAgentsSummary
    qa: OperationsQaSummary
