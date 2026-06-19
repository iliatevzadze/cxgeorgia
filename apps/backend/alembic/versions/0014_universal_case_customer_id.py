"""Link universal cases to workspace customers.

Revision ID: 0014
Revises: 0013
Create Date: 2026-06-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "universal_cases",
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_universal_cases_customer_id_customers",
        "universal_cases",
        "customers",
        ["customer_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_universal_cases_customer_id",
        "universal_cases",
        ["customer_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_universal_cases_customer_id",
        table_name="universal_cases",
    )
    op.drop_constraint(
        "fk_universal_cases_customer_id_customers",
        "universal_cases",
        type_="foreignkey",
    )
    op.drop_column("universal_cases", "customer_id")
