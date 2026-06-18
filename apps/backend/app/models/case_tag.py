"""Universal Case tag models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.universal_case import UniversalCase
    from app.models.workspace import Workspace


class CaseTag(Base):
    """Workspace-scoped tag that can be attached to Universal Cases."""

    __tablename__ = "case_tags"
    __table_args__ = (
        Index("ix_case_tags_workspace_id", "workspace_id"),
        Index("ix_case_tags_slug", "slug"),
        UniqueConstraint(
            "workspace_id",
            "slug",
            name="uq_case_tags_workspace_id_slug",
        ),
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
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100))
    color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    workspace: Mapped[Workspace] = relationship(back_populates="case_tags")
    cases: Mapped[list[UniversalCase]] = relationship(
        secondary="universal_case_tags",
        back_populates="tags",
    )


class UniversalCaseTag(Base):
    """Association between a Universal Case and a workspace tag."""

    __tablename__ = "universal_case_tags"
    __table_args__ = (
        Index("ix_universal_case_tags_case_id", "case_id"),
        Index("ix_universal_case_tags_tag_id", "tag_id"),
    )

    case_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("universal_cases.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("case_tags.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
