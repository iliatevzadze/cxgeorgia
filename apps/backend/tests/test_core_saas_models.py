"""Tests for core SaaS model columns, constraints, and relationships."""

import app.models  # noqa: F401 — ensure models are registered
from app.db.base import Base
from app.models.enums import (
    UserStatus,
    WorkspaceMemberRole,
    WorkspaceMemberStatus,
    WorkspaceStatus,
)
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_membership import WorkspaceMembership


def _column_names(table_name: str) -> set[str]:
    return {column.name for column in Base.metadata.tables[table_name].columns}


def _unique_constraints(table_name: str) -> list[tuple[str, ...]]:
    table = Base.metadata.tables[table_name]
    return [
        tuple(constraint.columns.keys())
        for constraint in table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    ]


def test_user_columns() -> None:
    assert _column_names("users") == {
        "id",
        "email",
        "full_name",
        "status",
        "is_email_verified",
        "created_at",
        "updated_at",
    }


def test_workspace_columns() -> None:
    assert _column_names("workspaces") == {
        "id",
        "name",
        "slug",
        "status",
        "created_at",
        "updated_at",
    }


def test_workspace_membership_columns() -> None:
    assert _column_names("workspace_memberships") == {
        "id",
        "workspace_id",
        "user_id",
        "role",
        "status",
        "created_at",
        "updated_at",
    }


def test_user_email_unique() -> None:
    email_column = Base.metadata.tables["users"].c.email
    assert email_column.unique is True


def test_workspace_slug_unique() -> None:
    slug_column = Base.metadata.tables["workspaces"].c.slug
    assert slug_column.unique is True


def test_workspace_membership_unique_workspace_user() -> None:
    constraints = _unique_constraints("workspace_memberships")
    assert ("workspace_id", "user_id") in constraints


def test_workspace_membership_indexes() -> None:
    indexes = Base.metadata.tables["workspace_memberships"].indexes
    index_columns = {tuple(index.columns.keys()) for index in indexes}
    assert ("workspace_id",) in index_columns
    assert ("user_id",) in index_columns
    assert ("workspace_id", "role") in index_columns


def test_user_memberships_relationship() -> None:
    assert User.memberships.property.back_populates == "user"


def test_workspace_memberships_relationship() -> None:
    assert Workspace.memberships.property.back_populates == "workspace"


def test_membership_user_relationship() -> None:
    assert WorkspaceMembership.user.property.back_populates == "memberships"


def test_membership_workspace_relationship() -> None:
    assert WorkspaceMembership.workspace.property.back_populates == "memberships"


def test_user_status_enum_values() -> None:
    assert {member.value for member in UserStatus} == {"active", "disabled"}


def test_workspace_status_enum_values() -> None:
    assert {member.value for member in WorkspaceStatus} == {"active", "disabled"}


def test_workspace_member_role_enum_values() -> None:
    assert {member.value for member in WorkspaceMemberRole} == {
        "owner",
        "admin",
        "member",
    }


def test_workspace_member_status_enum_values() -> None:
    assert {member.value for member in WorkspaceMemberStatus} == {"active", "removed"}
