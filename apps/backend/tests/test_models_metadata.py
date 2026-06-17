"""Tests for ORM model metadata registration."""

import app.models  # noqa: F401 — ensure models are registered
from app.db.base import Base


def test_users_table_in_metadata() -> None:
    assert "users" in Base.metadata.tables


def test_workspaces_table_in_metadata() -> None:
    assert "workspaces" in Base.metadata.tables


def test_workspace_memberships_table_in_metadata() -> None:
    assert "workspace_memberships" in Base.metadata.tables


def test_universal_cases_table_in_metadata() -> None:
    assert "universal_cases" in Base.metadata.tables
