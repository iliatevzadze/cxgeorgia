"""Saved Universal Case list views.

Revision ID: 0015
Revises: 0014
Create Date: 2026-06-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "case_list_views",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "filters",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("sort_by", sa.String(length=32), nullable=True),
        sa.Column("sort_order", sa.String(length=8), nullable=True),
        sa.Column("page_size", sa.Integer(), nullable=True),
        sa.Column(
            "is_default",
            sa.Boolean(),
            server_default=sa.text("false"),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "name",
            name="uq_case_list_views_workspace_id_name",
        ),
    )
    op.create_index(
        "ix_case_list_views_workspace_id",
        "case_list_views",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_list_views_created_by_user_id",
        "case_list_views",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_list_views_workspace_id_is_default",
        "case_list_views",
        ["workspace_id", "is_default"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_case_list_views_workspace_id_is_default",
        table_name="case_list_views",
    )
    op.drop_index(
        "ix_case_list_views_created_by_user_id",
        table_name="case_list_views",
    )
    op.drop_index(
        "ix_case_list_views_workspace_id",
        table_name="case_list_views",
    )
    op.drop_table("case_list_views")
