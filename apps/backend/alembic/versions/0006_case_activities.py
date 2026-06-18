"""Universal Case activity timeline table.

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-18

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

case_activity_type_enum = postgresql.ENUM(
    "case_created",
    "case_updated",
    "status_changed",
    "priority_changed",
    "assignment_changed",
    "comment_created",
    "comment_deleted",
    name="case_activity_type",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    case_activity_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "case_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("activity_type", case_activity_type_enum, nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=True),
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
            ["case_id"],
            ["universal_cases.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_case_activities_workspace_id",
        "case_activities",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_activities_case_id",
        "case_activities",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_activities_actor_user_id",
        "case_activities",
        ["actor_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_case_activities_actor_user_id",
        table_name="case_activities",
    )
    op.drop_index(
        "ix_case_activities_case_id",
        table_name="case_activities",
    )
    op.drop_index(
        "ix_case_activities_workspace_id",
        table_name="case_activities",
    )
    op.drop_table("case_activities")

    bind = op.get_bind()
    case_activity_type_enum.drop(bind, checkfirst=True)
