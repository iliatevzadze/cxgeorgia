"""Universal Case activity/timeline model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CaseActivityType

if TYPE_CHECKING:
    from app.models.universal_case import UniversalCase
    from app.models.user import User
    from app.models.workspace import Workspace


class CaseActivity(Base):
    """Workspace-scoped activity record for a Universal Case."""

    __tablename__ = "case_activities"
    __table_args__ = (
        Index("ix_case_activities_workspace_id", "workspace_id"),
        Index("ix_case_activities_case_id", "case_id"),
        Index("ix_case_activities_actor_user_id", "actor_user_id"),
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
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    activity_type: Mapped[CaseActivityType] = mapped_column(
        Enum(
            CaseActivityType,
            name="case_activity_type",
            values_callable=lambda enum: [member.value for member in enum],
        ),
    )
    activity_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    workspace: Mapped[Workspace] = relationship(back_populates="case_activities")
    case: Mapped[UniversalCase] = relationship(back_populates="activities")
    actor: Mapped[User | None] = relationship()
