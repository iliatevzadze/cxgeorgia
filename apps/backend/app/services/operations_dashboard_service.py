"""Operations dashboard aggregation helpers."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_case_metric import AgentCaseMetric
from app.models.agent_shift import AgentShift
from app.models.case_qa_review import CaseQaReview
from app.models.enums import CaseStatus, QaReviewStatus, SlaStatus
from app.models.universal_case import UniversalCase
from app.schemas.operations_dashboard import (
    OperationsAgentsSummary,
    OperationsCasesSummary,
    OperationsDashboardRead,
    OperationsQaSummary,
    OperationsSlaSummary,
)


async def get_operations_dashboard(
    session: AsyncSession,
    workspace_id: UUID,
) -> OperationsDashboardRead:
    """Aggregate operational metrics for a workspace."""
    cases_row = (
        await session.execute(
            select(
                func.count(UniversalCase.id),
                func.count().filter(UniversalCase.status == CaseStatus.OPEN),
                func.count().filter(UniversalCase.status == CaseStatus.PENDING),
                func.count().filter(UniversalCase.status == CaseStatus.RESOLVED),
                func.count().filter(UniversalCase.sla_status == SlaStatus.ON_TRACK),
                func.count().filter(UniversalCase.sla_status == SlaStatus.AT_RISK),
                func.count().filter(UniversalCase.sla_status == SlaStatus.BREACHED),
            ).where(UniversalCase.workspace_id == workspace_id)
        )
    ).one()

    active_shifts = int(
        await session.scalar(
            select(func.count())
            .select_from(AgentShift)
            .where(
                AgentShift.workspace_id == workspace_id,
                AgentShift.is_active.is_(True),
            )
        )
        or 0
    )
    total_agent_case_metrics = int(
        await session.scalar(
            select(func.count())
            .select_from(AgentCaseMetric)
            .where(AgentCaseMetric.workspace_id == workspace_id)
        )
        or 0
    )
    total_agent_messages = int(
        await session.scalar(
            select(func.coalesce(func.sum(AgentCaseMetric.messages_count), 0)).where(
                AgentCaseMetric.workspace_id == workspace_id,
            )
        )
        or 0
    )

    qa_row = (
        await session.execute(
            select(
                func.count(CaseQaReview.id),
                func.count().filter(CaseQaReview.status == QaReviewStatus.PENDING),
                func.count().filter(CaseQaReview.status == QaReviewStatus.APPROVED),
                func.count().filter(CaseQaReview.status == QaReviewStatus.REJECTED),
                func.avg(CaseQaReview.score),
            ).where(CaseQaReview.workspace_id == workspace_id)
        )
    ).one()

    return OperationsDashboardRead(
        cases=OperationsCasesSummary(
            total_cases=int(cases_row[0]),
            open_cases=int(cases_row[1]),
            pending_cases=int(cases_row[2]),
            resolved_cases=int(cases_row[3]),
        ),
        sla=OperationsSlaSummary(
            on_track=int(cases_row[4]),
            at_risk=int(cases_row[5]),
            breached=int(cases_row[6]),
        ),
        agents=OperationsAgentsSummary(
            active_shifts=active_shifts,
            total_agent_case_metrics=total_agent_case_metrics,
            total_agent_messages=total_agent_messages,
        ),
        qa=OperationsQaSummary(
            total_reviews=int(qa_row[0]),
            pending_reviews=int(qa_row[1]),
            approved_reviews=int(qa_row[2]),
            rejected_reviews=int(qa_row[3]),
            average_score=float(qa_row[4] or 0),
        ),
    )
