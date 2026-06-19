"""Case QA review and criteria score tables.

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "case_qa_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "reviewed_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "reviewed_agent_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "score",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("overall_comment", sa.Text(), nullable=True),
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
        sa.CheckConstraint(
            "score >= 0 AND score <= 100",
            name="ck_case_qa_reviews_score_range",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_case_qa_reviews_status",
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
            ["reviewed_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_agent_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_case_qa_reviews_workspace_id",
        "case_qa_reviews",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_qa_reviews_case_id",
        "case_qa_reviews",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_qa_reviews_reviewed_by_user_id",
        "case_qa_reviews",
        ["reviewed_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_qa_reviews_reviewed_agent_user_id",
        "case_qa_reviews",
        ["reviewed_agent_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_qa_reviews_status",
        "case_qa_reviews",
        ["status"],
        unique=False,
    )

    op.create_table(
        "case_qa_criteria_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("qa_review_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("criterion_name", sa.String(length=128), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "score >= 0 AND score <= 100",
            name="ck_case_qa_criteria_scores_score_range",
        ),
        sa.ForeignKeyConstraint(
            ["qa_review_id"],
            ["case_qa_reviews.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_case_qa_criteria_scores_qa_review_id",
        "case_qa_criteria_scores",
        ["qa_review_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_case_qa_criteria_scores_qa_review_id",
        table_name="case_qa_criteria_scores",
    )
    op.drop_table("case_qa_criteria_scores")
    op.drop_index(
        "ix_case_qa_reviews_status",
        table_name="case_qa_reviews",
    )
    op.drop_index(
        "ix_case_qa_reviews_reviewed_agent_user_id",
        table_name="case_qa_reviews",
    )
    op.drop_index(
        "ix_case_qa_reviews_reviewed_by_user_id",
        table_name="case_qa_reviews",
    )
    op.drop_index(
        "ix_case_qa_reviews_case_id",
        table_name="case_qa_reviews",
    )
    op.drop_index(
        "ix_case_qa_reviews_workspace_id",
        table_name="case_qa_reviews",
    )
    op.drop_table("case_qa_reviews")
