"""Workspace customer record model."""

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
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CustomerStatus

if TYPE_CHECKING:
    from app.models.universal_case import UniversalCase
    from app.models.workspace import Workspace


class Customer(Base):
    """Workspace-scoped customer record."""

    __tablename__ = "customers"
    __table_args__ = (
        Index("ix_customers_workspace_id", "workspace_id"),
        Index("ix_customers_email", "email"),
        Index(
            "uq_customers_workspace_id_email",
            "workspace_id",
            "email",
            unique=True,
            postgresql_where=text("email IS NOT NULL"),
        ),
        Index(
            "uq_customers_workspace_id_external_id",
            "workspace_id",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
        CheckConstraint(
            "status IN ('active', 'archived')",
            name="ck_customers_status",
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
    display_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    locale: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CustomerStatus] = mapped_column(
        Enum(
            CustomerStatus,
            native_enum=False,
            length=32,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=CustomerStatus.ACTIVE,
        server_default=CustomerStatus.ACTIVE.value,
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

    workspace: Mapped[Workspace] = relationship(back_populates="customers")
    universal_cases: Mapped[list[UniversalCase]] = relationship(
        back_populates="customer",
    )
