"""Tests for Universal Case model metadata, constraints, and enums."""

import app.models  # noqa: F401 — ensure models are registered
from app.db.base import Base
from app.models.enums import CasePriority, CaseSource, CaseStatus
from app.models.universal_case import UniversalCase
from app.models.workspace import Workspace


def _column_names(table_name: str) -> set[str]:
    return {column.name for column in Base.metadata.tables[table_name].columns}


def _foreign_key_targets(table_name: str, column_name: str) -> set[str]:
    column = Base.metadata.tables[table_name].c[column_name]
    return {fk.column.table.name for fk in column.foreign_keys}


def test_universal_cases_columns() -> None:
    assert _column_names("universal_cases") == {
        "id",
        "workspace_id",
        "title",
        "description",
        "status",
        "priority",
        "source",
        "customer_name",
        "customer_email",
        "external_reference",
        "created_by_user_id",
        "assigned_to_user_id",
        "customer_id",
        "created_at",
        "updated_at",
        "first_response_due_at",
        "first_response_at",
        "resolution_due_at",
        "resolved_at",
        "sla_status",
    }


def test_universal_cases_workspace_fk() -> None:
    assert _foreign_key_targets("universal_cases", "workspace_id") == {"workspaces"}


def test_universal_cases_created_by_user_fk() -> None:
    assert _foreign_key_targets("universal_cases", "created_by_user_id") == {"users"}


def test_universal_cases_assigned_to_user_fk() -> None:
    assert _foreign_key_targets("universal_cases", "assigned_to_user_id") == {"users"}


def test_universal_cases_customer_fk() -> None:
    assert _foreign_key_targets("universal_cases", "customer_id") == {"customers"}


def test_universal_cases_indexes() -> None:
    indexes = Base.metadata.tables["universal_cases"].indexes
    index_columns = {tuple(index.columns.keys()) for index in indexes}
    assert ("workspace_id",) in index_columns
    assert ("workspace_id", "status") in index_columns
    assert ("sla_status",) in index_columns
    assert ("resolution_due_at",) in index_columns
    assert ("customer_id",) in index_columns


def test_universal_case_workspace_relationship() -> None:
    assert UniversalCase.workspace.property.back_populates == "universal_cases"
    assert Workspace.universal_cases.property.back_populates == "workspace"


def test_universal_case_customer_relationship() -> None:
    from app.models.customer import Customer

    assert UniversalCase.customer.property.back_populates == "universal_cases"
    assert Customer.universal_cases.property.back_populates == "customer"


def test_case_status_enum_values() -> None:
    assert {member.value for member in CaseStatus} == {
        "open",
        "pending",
        "resolved",
        "closed",
    }


def test_case_priority_enum_values() -> None:
    assert {member.value for member in CasePriority} == {
        "low",
        "normal",
        "high",
        "urgent",
    }


def test_case_source_enum_values() -> None:
    assert {member.value for member in CaseSource} == {
        "manual",
        "email",
        "chat",
        "phone",
        "web",
        "import",
    }
