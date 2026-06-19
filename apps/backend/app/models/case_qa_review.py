"""Case QA review model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import QaReviewStatus

if TYPE_CHECKING:
    from app.models.case_qa_criteria_score import CaseQaCriteriaScore
    from app.models.universal_case import UniversalCase
    from app.models.user import User
    from app.models.workspace import Workspace


class CaseQaReview(Base):
    """Structured QA evaluation of a Universal Case."""

    __tablename__ = "case_qa_reviews"
    __table_args__ = (
        CheckConstraint(
            "score >= 0 AND score <= 100",
            name="ck_case_qa_reviews_score_range",
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_case_qa_reviews_status",
        ),
        Index("ix_case_qa_reviews_workspace_id", "workspace_id"),
        Index("ix_case_qa_reviews_case_id", "case_id"),
        Index("ix_case_qa_reviews_reviewed_by_user_id", "reviewed_by_user_id"),
        Index("ix_case_qa_reviews_reviewed_agent_user_id", "reviewed_agent_user_id"),
        Index("ix_case_qa_reviews_status", "status"),
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
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_agent_user_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
    )
    status: Mapped[QaReviewStatus] = mapped_column(
        Enum(
            QaReviewStatus,
            native_enum=False,
            length=32,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=QaReviewStatus.PENDING,
        server_default=QaReviewStatus.PENDING.value,
    )
    overall_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    workspace: Mapped[Workspace] = relationship(back_populates="case_qa_reviews")
    case: Mapped[UniversalCase] = relationship(back_populates="qa_reviews")
    reviewed_by: Mapped[User | None] = relationship(
        back_populates="qa_reviews_reviewed_by",
        foreign_keys=[reviewed_by_user_id],
    )
    reviewed_agent: Mapped[User | None] = relationship(
        back_populates="qa_reviews_reviewed_agent",
        foreign_keys=[reviewed_agent_user_id],
    )
    criteria_scores: Mapped[list[CaseQaCriteriaScore]] = relationship(
        back_populates="qa_review",
        cascade="all, delete-orphan",
    )
