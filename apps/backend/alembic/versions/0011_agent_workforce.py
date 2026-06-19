"""Agent workforce shift and case metrics tables.

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_shifts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clock_in_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("clock_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
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
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_agent_shifts_workspace_id",
        "agent_shifts",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_agent_shifts_user_id",
        "agent_shifts",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_agent_shifts_is_active",
        "agent_shifts",
        ["is_active"],
        unique=False,
    )

    op.create_table(
        "agent_case_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_response_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "messages_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["universal_cases.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_agent_case_metrics_workspace_id",
        "agent_case_metrics",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_agent_case_metrics_case_id",
        "agent_case_metrics",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        "ix_agent_case_metrics_user_id",
        "agent_case_metrics",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agent_case_metrics_user_id",
        table_name="agent_case_metrics",
    )
    op.drop_index(
        "ix_agent_case_metrics_case_id",
        table_name="agent_case_metrics",
    )
    op.drop_index(
        "ix_agent_case_metrics_workspace_id",
        table_name="agent_case_metrics",
    )
    op.drop_table("agent_case_metrics")
    op.drop_index(
        "ix_agent_shifts_is_active",
        table_name="agent_shifts",
    )
    op.drop_index(
        "ix_agent_shifts_user_id",
        table_name="agent_shifts",
    )
    op.drop_index(
        "ix_agent_shifts_workspace_id",
        table_name="agent_shifts",
    )
    op.drop_table("agent_shifts")
