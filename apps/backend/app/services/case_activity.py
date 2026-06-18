"""Case activity recording helpers."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_activity import CaseActivity
from app.models.enums import CaseActivityType
from app.models.universal_case import UniversalCase
from app.schemas.universal_case import UniversalCaseUpdate

CASE_UPDATED_FIELDS = frozenset(
    {
        "title",
        "description",
        "source",
        "customer_name",
        "customer_email",
        "external_reference",
    }
)


def snapshot_case(case: UniversalCase) -> dict[str, Any]:
    """Capture case field values before a PATCH for activity diffing."""
    return {
        "title": case.title,
        "description": case.description,
        "status": case.status,
        "priority": case.priority,
        "source": case.source,
        "customer_name": case.customer_name,
        "customer_email": case.customer_email,
        "external_reference": case.external_reference,
        "assigned_to_user_id": case.assigned_to_user_id,
    }


def _enum_value(value: object) -> object:
    if hasattr(value, "value"):
        return value.value
    return value


def _uuid_value(value: UUID | None) -> str | None:
    if value is None:
        return None
    return str(value)


def record_case_activity(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    case_id: UUID,
    actor_user_id: UUID | None,
    activity_type: CaseActivityType,
    message: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> CaseActivity:
    activity = CaseActivity(
        workspace_id=workspace_id,
        case_id=case_id,
        actor_user_id=actor_user_id,
        activity_type=activity_type,
        message=message,
        activity_metadata=metadata or {},
    )
    session.add(activity)
    return activity


def record_case_created_activity(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    case: UniversalCase,
    actor_user_id: UUID,
) -> CaseActivity:
    return record_case_activity(
        session,
        workspace_id=workspace_id,
        case_id=case.id,
        actor_user_id=actor_user_id,
        activity_type=CaseActivityType.CASE_CREATED,
        message="Case created",
        metadata={
            "title": case.title,
            "status": case.status.value,
            "priority": case.priority.value,
            "source": case.source.value,
        },
    )


def _patch_fields_in_body(body: UniversalCaseUpdate) -> set[str]:
    fields: set[str] = set()
    if "title" in body.model_fields_set and body.title is not None:
        fields.add("title")
    if "description" in body.model_fields_set:
        fields.add("description")
    if body.status is not None:
        fields.add("status")
    if body.priority is not None:
        fields.add("priority")
    if body.source is not None:
        fields.add("source")
    if "customer_name" in body.model_fields_set:
        fields.add("customer_name")
    if "customer_email" in body.model_fields_set:
        fields.add("customer_email")
    if "external_reference" in body.model_fields_set:
        fields.add("external_reference")
    if "assigned_to_user_id" in body.model_fields_set:
        fields.add("assigned_to_user_id")
    return fields


def record_case_patch_activities(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    case: UniversalCase,
    actor_user_id: UUID,
    before: dict[str, Any],
    body: UniversalCaseUpdate,
) -> list[CaseActivity]:
    after = snapshot_case(case)
    patch_fields = _patch_fields_in_body(body)
    activities: list[CaseActivity] = []

    if "status" in patch_fields and before["status"] != after["status"]:
        activities.append(
            record_case_activity(
                session,
                workspace_id=workspace_id,
                case_id=case.id,
                actor_user_id=actor_user_id,
                activity_type=CaseActivityType.STATUS_CHANGED,
                message="Status changed",
                metadata={
                    "from": _enum_value(before["status"]),
                    "to": _enum_value(after["status"]),
                },
            )
        )

    if "priority" in patch_fields and before["priority"] != after["priority"]:
        activities.append(
            record_case_activity(
                session,
                workspace_id=workspace_id,
                case_id=case.id,
                actor_user_id=actor_user_id,
                activity_type=CaseActivityType.PRIORITY_CHANGED,
                message="Priority changed",
                metadata={
                    "from": _enum_value(before["priority"]),
                    "to": _enum_value(after["priority"]),
                },
            )
        )

    if (
        "assigned_to_user_id" in patch_fields
        and before["assigned_to_user_id"] != after["assigned_to_user_id"]
    ):
        from_id = before["assigned_to_user_id"]
        to_id = after["assigned_to_user_id"]
        if from_id is None and to_id is not None:
            message = "Case assigned"
        elif from_id is not None and to_id is None:
            message = "Case unassigned"
        else:
            message = "Case reassigned"
        activities.append(
            record_case_activity(
                session,
                workspace_id=workspace_id,
                case_id=case.id,
                actor_user_id=actor_user_id,
                activity_type=CaseActivityType.ASSIGNMENT_CHANGED,
                message=message,
                metadata={
                    "from": _uuid_value(from_id),
                    "to": _uuid_value(to_id),
                },
            )
        )

    changed_generic_fields = [
        field
        for field in CASE_UPDATED_FIELDS
        if field in patch_fields and before[field] != after[field]
    ]
    if changed_generic_fields:
        activities.append(
            record_case_activity(
                session,
                workspace_id=workspace_id,
                case_id=case.id,
                actor_user_id=actor_user_id,
                activity_type=CaseActivityType.CASE_UPDATED,
                message="Case updated",
                metadata={"changed_fields": changed_generic_fields},
            )
        )

    return activities


def record_comment_created_activity(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    case_id: UUID,
    actor_user_id: UUID,
    comment_id: UUID,
    is_internal: bool,
) -> CaseActivity:
    return record_case_activity(
        session,
        workspace_id=workspace_id,
        case_id=case_id,
        actor_user_id=actor_user_id,
        activity_type=CaseActivityType.COMMENT_CREATED,
        message="Comment added",
        metadata={
            "comment_id": str(comment_id),
            "is_internal": is_internal,
        },
    )


def record_comment_deleted_activity(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    case_id: UUID,
    actor_user_id: UUID,
    comment_id: UUID,
    is_internal: bool,
) -> CaseActivity:
    return record_case_activity(
        session,
        workspace_id=workspace_id,
        case_id=case_id,
        actor_user_id=actor_user_id,
        activity_type=CaseActivityType.COMMENT_DELETED,
        message="Comment deleted",
        metadata={
            "comment_id": str(comment_id),
            "is_internal": is_internal,
        },
    )
