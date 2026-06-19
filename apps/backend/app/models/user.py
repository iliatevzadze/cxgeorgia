"""User model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserStatus

if TYPE_CHECKING:
    from app.models.agent_case_metric import AgentCaseMetric
    from app.models.agent_shift import AgentShift
    from app.models.case_list_view import CaseListView
    from app.models.case_qa_review import CaseQaReview
    from app.models.workspace_membership import WorkspaceMembership


class User(Base):
    """Platform user."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[UserStatus] = mapped_column(
        Enum(
            UserStatus,
            name="user_status",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=UserStatus.ACTIVE,
        server_default=UserStatus.ACTIVE.value,
    )
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
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
        back_populates="user",
        cascade="all, delete-orphan",
    )
    agent_shifts: Mapped[list[AgentShift]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    agent_case_metrics: Mapped[list[AgentCaseMetric]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    qa_reviews_reviewed_by: Mapped[list[CaseQaReview]] = relationship(
        back_populates="reviewed_by",
        foreign_keys="CaseQaReview.reviewed_by_user_id",
    )
    qa_reviews_reviewed_agent: Mapped[list[CaseQaReview]] = relationship(
        back_populates="reviewed_agent",
        foreign_keys="CaseQaReview.reviewed_agent_user_id",
    )
    case_list_views: Mapped[list[CaseListView]] = relationship(
        back_populates="created_by_user",
    )
