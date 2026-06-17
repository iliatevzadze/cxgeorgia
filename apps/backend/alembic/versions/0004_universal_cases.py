"""Universal Case table and enums.

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-17

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

case_status_enum = postgresql.ENUM(
    "open",
    "pending",
    "resolved",
    "closed",
    name="case_status",
    create_type=False,
)
case_priority_enum = postgresql.ENUM(
    "low",
    "normal",
    "high",
    "urgent",
    name="case_priority",
    create_type=False,
)
case_source_enum = postgresql.ENUM(
    "manual",
    "email",
    "chat",
    "phone",
    "web",
    "import",
    name="case_source",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    case_status_enum.create(bind, checkfirst=True)
    case_priority_enum.create(bind, checkfirst=True)
    case_source_enum.create(bind, checkfirst=True)

    op.create_table(
        "universal_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            case_status_enum,
            server_default="open",
            nullable=False,
        ),
        sa.Column(
            "priority",
            case_priority_enum,
            server_default="normal",
            nullable=False,
        ),
        sa.Column(
            "source",
            case_source_enum,
            server_default="manual",
            nullable=False,
        ),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("customer_email", sa.String(length=320), nullable=True),
        sa.Column("external_reference", sa.String(length=255), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_to_user_id", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_to_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_universal_cases_workspace_id",
        "universal_cases",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_universal_cases_workspace_id_status",
        "universal_cases",
        ["workspace_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_universal_cases_workspace_id_status",
        table_name="universal_cases",
    )
    op.drop_index(
        "ix_universal_cases_workspace_id",
        table_name="universal_cases",
    )
    op.drop_table("universal_cases")

    bind = op.get_bind()
    case_source_enum.drop(bind, checkfirst=True)
    case_priority_enum.drop(bind, checkfirst=True)
    case_status_enum.drop(bind, checkfirst=True)
