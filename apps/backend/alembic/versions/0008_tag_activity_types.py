"""Add tag activity enum values.

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-18

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ORIGINAL_CASE_ACTIVITY_TYPES = (
    "case_created",
    "case_updated",
    "status_changed",
    "priority_changed",
    "assignment_changed",
    "comment_created",
    "comment_deleted",
)


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE case_activity_type ADD VALUE IF NOT EXISTS 'tag_attached'"
        )
        op.execute(
            "ALTER TYPE case_activity_type ADD VALUE IF NOT EXISTS 'tag_detached'"
        )


def downgrade() -> None:
    op.execute(
        "DELETE FROM case_activities "
        "WHERE activity_type::text IN ('tag_attached', 'tag_detached')"
    )
    op.execute("ALTER TYPE case_activity_type RENAME TO case_activity_type_old")
    original_values = ", ".join(f"'{value}'" for value in _ORIGINAL_CASE_ACTIVITY_TYPES)
    op.execute(f"CREATE TYPE case_activity_type AS ENUM ({original_values})")
    op.execute(
        "ALTER TABLE case_activities "
        "ALTER COLUMN activity_type TYPE case_activity_type "
        "USING activity_type::text::case_activity_type"
    )
    op.execute("DROP TYPE case_activity_type_old")
