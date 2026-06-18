"""Universal Case comment model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.universal_case import UniversalCase
    from app.models.user import User
    from app.models.workspace import Workspace


class CaseComment(Base):
    """Workspace-scoped comment on a Universal Case."""

    __tablename__ = "case_comments"
    __table_args__ = (
        Index("ix_case_comments_workspace_id", "workspace_id"),
        Index("ix_case_comments_case_id", "case_id"),
        Index("ix_case_comments_author_user_id", "author_user_id"),
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
    author_user_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    body: Mapped[str] = mapped_column(Text)
    is_internal: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
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

    workspace: Mapped[Workspace] = relationship(back_populates="case_comments")
    case: Mapped[UniversalCase] = relationship(back_populates="comments")
    author: Mapped[User | None] = relationship()
