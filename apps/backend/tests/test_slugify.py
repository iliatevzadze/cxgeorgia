"""Tests for workspace slug helper."""

from app.core.slugify import slugify_workspace_name


def test_slugify_workspace_name_basic() -> None:
    assert slugify_workspace_name("Acme Support") == "acme-support"


def test_slugify_workspace_name_trims_and_collapses_whitespace() -> None:
    assert slugify_workspace_name("  Georgian CX  ") == "georgian-cx"


def test_slugify_workspace_name_removes_unsafe_characters() -> None:
    assert slugify_workspace_name("Workspace!!!") == "workspace"


def test_slugify_workspace_name_empty_fallback() -> None:
    assert slugify_workspace_name("!!!") == "workspace"
