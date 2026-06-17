"""Workspace name slug helpers."""

import re

_SLUG_FALLBACK = "workspace"
_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def slugify_workspace_name(name: str) -> str:
    """Convert a workspace name into an ASCII-safe URL slug."""
    normalized = name.strip().lower()
    slug = _SLUG_PATTERN.sub("-", normalized).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or _SLUG_FALLBACK
