"""Shared enum types for core SaaS models."""

from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class WorkspaceStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class WorkspaceMemberRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class WorkspaceMemberStatus(StrEnum):
    ACTIVE = "active"
    REMOVED = "removed"


class CaseStatus(StrEnum):
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"


class CasePriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class CaseSource(StrEnum):
    MANUAL = "manual"
    EMAIL = "email"
    CHAT = "chat"
    PHONE = "phone"
    WEB = "web"
    IMPORT = "import"
