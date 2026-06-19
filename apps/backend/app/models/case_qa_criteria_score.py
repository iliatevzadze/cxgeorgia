"""Case QA criteria score model."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.case_qa_review import CaseQaReview


class CaseQaCriteriaScore(Base):
    """Individual criterion score within a QA review."""

    __tablename__ = "case_qa_criteria_scores"
    __table_args__ = (
        CheckConstraint(
            "score >= 0 AND score <= 100",
            name="ck_case_qa_criteria_scores_score_range",
        ),
        Index("ix_case_qa_criteria_scores_qa_review_id", "qa_review_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    qa_review_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("case_qa_reviews.id", ondelete="CASCADE"),
    )
    criterion_name: Mapped[str] = mapped_column(String(128))
    score: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    qa_review: Mapped[CaseQaReview] = relationship(back_populates="criteria_scores")
