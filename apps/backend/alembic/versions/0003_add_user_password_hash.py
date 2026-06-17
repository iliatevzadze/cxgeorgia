"""Add password_hash to users.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-17

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Unusable bcrypt hash for any pre-existing rows without a password (local dev only).
UNUSABLE_PASSWORD_HASH = (
    "$2b$12$UGLWvku5/q9knaabiSGcFOq5vn9LRTqjEYCVzEaQL7R7UcNfO4ZLO"
)


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=255), nullable=True),
    )
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "UPDATE users SET password_hash = :hash WHERE password_hash IS NULL"
        ),
        {"hash": UNUSABLE_PASSWORD_HASH},
    )
    op.alter_column("users", "password_hash", nullable=False)


def downgrade() -> None:
    op.drop_column("users", "password_hash")
