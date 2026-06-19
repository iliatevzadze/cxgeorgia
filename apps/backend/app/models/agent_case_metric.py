"""Per-case agent performance metrics."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.universal_case import UniversalCase
    from app.models.user import User
    from app.models.workspace import Workspace


class AgentCaseMetric(Base):
    """Lightweight per-agent metrics for a Universal Case."""

    __tablename__ = "agent_case_metrics"
    __table_args__ = (
        Index("ix_agent_case_metrics_workspace_id", "workspace_id"),
        Index("ix_agent_case_metrics_case_id", "case_id"),
        Index("ix_agent_case_metrics_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    workspace_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
    )
    case_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("universal_cases.id", ondelete="CASCADE"),
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    assigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    first_response_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    messages_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
    )

    workspace: Mapped[Workspace] = relationship(back_populates="agent_case_metrics")
    case: Mapped[UniversalCase] = relationship(back_populates="agent_metrics")
    user: Mapped[User] = relationship(back_populates="agent_case_metrics")
