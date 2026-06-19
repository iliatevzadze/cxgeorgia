"""Universal Case SLA tracking columns.

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-19

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "universal_cases",
        sa.Column("first_response_due_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "universal_cases",
        sa.Column("first_response_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "universal_cases",
        sa.Column("resolution_due_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "universal_cases",
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "universal_cases",
        sa.Column(
            "sla_status",
            sa.String(length=32),
            server_default="on_track",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_universal_cases_sla_status",
        "universal_cases",
        "sla_status IN ('on_track', 'at_risk', 'breached')",
    )
    op.create_index(
        "ix_universal_cases_sla_status",
        "universal_cases",
        ["sla_status"],
        unique=False,
    )
    op.create_index(
        "ix_universal_cases_resolution_due_at",
        "universal_cases",
        ["resolution_due_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_universal_cases_resolution_due_at",
        table_name="universal_cases",
    )
    op.drop_index(
        "ix_universal_cases_sla_status",
        table_name="universal_cases",
    )
    op.drop_constraint(
        "ck_universal_cases_sla_status",
        "universal_cases",
        type_="check",
    )
    op.drop_column("universal_cases", "sla_status")
    op.drop_column("universal_cases", "resolved_at")
    op.drop_column("universal_cases", "resolution_due_at")
    op.drop_column("universal_cases", "first_response_at")
    op.drop_column("universal_cases", "first_response_due_at")
