"""Workspace model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import WorkspaceStatus

if TYPE_CHECKING:
    from app.models.agent_case_metric import AgentCaseMetric
    from app.models.agent_shift import AgentShift
    from app.models.case_activity import CaseActivity
    from app.models.case_attachment import CaseAttachment
    from app.models.case_comment import CaseComment
    from app.models.case_qa_review import CaseQaReview
    from app.models.case_tag import CaseTag
    from app.models.universal_case import UniversalCase
    from app.models.workspace_membership import WorkspaceMembership


class Workspace(Base):
    """Tenant workspace."""

    __tablename__ = "workspaces"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    status: Mapped[WorkspaceStatus] = mapped_column(
        Enum(
            WorkspaceStatus,
            name="workspace_status",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=WorkspaceStatus.ACTIVE,
        server_default=WorkspaceStatus.ACTIVE.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    memberships: Mapped[list[WorkspaceMembership]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    universal_cases: Mapped[list[UniversalCase]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    case_comments: Mapped[list[CaseComment]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    case_activities: Mapped[list[CaseActivity]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    case_tags: Mapped[list[CaseTag]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    case_attachments: Mapped[list[CaseAttachment]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    agent_shifts: Mapped[list[AgentShift]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    agent_case_metrics: Mapped[list[AgentCaseMetric]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    case_qa_reviews: Mapped[list[CaseQaReview]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
