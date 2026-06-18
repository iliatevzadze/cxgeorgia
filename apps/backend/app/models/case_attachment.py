"""Universal Case attachment model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.universal_case import UniversalCase
    from app.models.user import User
    from app.models.workspace import Workspace


class CaseAttachment(Base):
    """Workspace-scoped file attachment on a Universal Case."""

    __tablename__ = "case_attachments"
    __table_args__ = (
        Index("ix_case_attachments_workspace_id", "workspace_id"),
        Index("ix_case_attachments_case_id", "case_id"),
        Index("ix_case_attachments_uploaded_by_user_id", "uploaded_by_user_id"),
        UniqueConstraint(
            "storage_bucket",
            "storage_key",
            name="uq_case_attachments_storage_bucket_storage_key",
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
    case_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("universal_cases.id", ondelete="CASCADE"),
    )
    uploaded_by_user_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    file_name: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    storage_bucket: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(1024))
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    workspace: Mapped[Workspace] = relationship(back_populates="case_attachments")
    case: Mapped[UniversalCase] = relationship(back_populates="attachments")
    uploaded_by: Mapped[User | None] = relationship()
