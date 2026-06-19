"""Customer records table.

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("locale", sa.String(length=32), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('active', 'archived')",
            name="ck_customers_status",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_customers_workspace_id",
        "customers",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_customers_email",
        "customers",
        ["email"],
        unique=False,
    )
    op.create_index(
        "uq_customers_workspace_id_email",
        "customers",
        ["workspace_id", "email"],
        unique=True,
        postgresql_where=sa.text("email IS NOT NULL"),
    )
    op.create_index(
        "uq_customers_workspace_id_external_id",
        "customers",
        ["workspace_id", "external_id"],
        unique=True,
        postgresql_where=sa.text("external_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_customers_workspace_id_external_id",
        table_name="customers",
    )
    op.drop_index(
        "uq_customers_workspace_id_email",
        table_name="customers",
    )
    op.drop_index(
        "ix_customers_email",
        table_name="customers",
    )
    op.drop_index(
        "ix_customers_workspace_id",
        table_name="customers",
    )
    op.drop_table("customers")
