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


class CaseActivityType(StrEnum):
    CASE_CREATED = "case_created"
    CASE_UPDATED = "case_updated"
    STATUS_CHANGED = "status_changed"
    PRIORITY_CHANGED = "priority_changed"
    ASSIGNMENT_CHANGED = "assignment_changed"
    COMMENT_CREATED = "comment_created"
    COMMENT_DELETED = "comment_deleted"
