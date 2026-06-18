"""Universal Case comments table.

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-18

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "case_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "is_internal",
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
            ["case_id"],
            ["universal_cases.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["author_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_case_comments_workspace_id",
        "case_comments",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_comments_case_id",
        "case_comments",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_comments_author_user_id",
        "case_comments",
        ["author_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_case_comments_author_user_id",
        table_name="case_comments",
    )
    op.drop_index(
        "ix_case_comments_case_id",
        table_name="case_comments",
    )
    op.drop_index(
        "ix_case_comments_workspace_id",
        table_name="case_comments",
    )
    op.drop_table("case_comments")
