"""Universal Case model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CasePriority, CaseSource, CaseStatus

if TYPE_CHECKING:
    from app.models.case_comment import CaseComment
    from app.models.workspace import Workspace


class UniversalCase(Base):
    """Workspace-scoped customer issue or work item."""

    __tablename__ = "universal_cases"
    __table_args__ = (
        Index("ix_universal_cases_workspace_id", "workspace_id"),
        Index("ix_universal_cases_workspace_id_status", "workspace_id", "status"),
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
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CaseStatus] = mapped_column(
        Enum(
            CaseStatus,
            name="case_status",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=CaseStatus.OPEN,
        server_default=CaseStatus.OPEN.value,
    )
    priority: Mapped[CasePriority] = mapped_column(
        Enum(
            CasePriority,
            name="case_priority",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=CasePriority.NORMAL,
        server_default=CasePriority.NORMAL.value,
    )
    source: Mapped[CaseSource] = mapped_column(
        Enum(
            CaseSource,
            name="case_source",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=CaseSource.MANUAL,
        server_default=CaseSource.MANUAL.value,
    )
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_to_user_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
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

    workspace: Mapped[Workspace] = relationship(back_populates="universal_cases")
    comments: Mapped[list[CaseComment]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
