"""Saved Universal Case list view model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace


class CaseListView(Base):
    """Workspace-scoped saved case list view."""

    __tablename__ = "case_list_views"
    __table_args__ = (
        Index("ix_case_list_views_workspace_id", "workspace_id"),
        Index("ix_case_list_views_created_by_user_id", "created_by_user_id"),
        Index(
            "uq_case_list_views_workspace_id_name",
            "workspace_id",
            "name",
            unique=True,
        ),
        Index(
            "ix_case_list_views_workspace_id_is_default",
            "workspace_id",
            "is_default",
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
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    filters: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    sort_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sort_order: Mapped[str | None] = mapped_column(String(8), nullable=True)
    page_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
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

    workspace: Mapped[Workspace] = relationship(back_populates="case_list_views")
    created_by_user: Mapped[User | None] = relationship(
        back_populates="case_list_views",
    )
