"""Universal Case attachments table.

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-18

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "case_attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("file_name", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_bucket", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
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
            ["uploaded_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "storage_bucket",
            "storage_key",
            name="uq_case_attachments_storage_bucket_storage_key",
        ),
    )
    op.create_index(
        "ix_case_attachments_workspace_id",
        "case_attachments",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_attachments_case_id",
        "case_attachments",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_attachments_uploaded_by_user_id",
        "case_attachments",
        ["uploaded_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_case_attachments_uploaded_by_user_id",
        table_name="case_attachments",
    )
    op.drop_index(
        "ix_case_attachments_case_id",
        table_name="case_attachments",
    )
    op.drop_index(
        "ix_case_attachments_workspace_id",
        table_name="case_attachments",
    )
    op.drop_table("case_attachments")
