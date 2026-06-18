"""Universal Case tags tables.

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-18

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "case_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=32), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "slug",
            name="uq_case_tags_workspace_id_slug",
        ),
    )
    op.create_index(
        "ix_case_tags_workspace_id",
        "case_tags",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_tags_slug",
        "case_tags",
        ["slug"],
        unique=False,
    )

    op.create_table(
        "universal_case_tags",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["universal_cases.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["case_tags.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("case_id", "tag_id"),
    )
    op.create_index(
        "ix_universal_case_tags_case_id",
        "universal_case_tags",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        "ix_universal_case_tags_tag_id",
        "universal_case_tags",
        ["tag_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_universal_case_tags_tag_id",
        table_name="universal_case_tags",
    )
    op.drop_index(
        "ix_universal_case_tags_case_id",
        table_name="universal_case_tags",
    )
    op.drop_table("universal_case_tags")

    op.drop_index(
        "ix_case_tags_slug",
        table_name="case_tags",
    )
    op.drop_index(
        "ix_case_tags_workspace_id",
        table_name="case_tags",
    )
    op.drop_table("case_tags")
