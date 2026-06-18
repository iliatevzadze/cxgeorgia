"""Tests for Universal Case activity model metadata and persistence."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import app.models  # noqa: F401 — ensure models are registered
from app.db.base import Base
from app.models.case_activity import CaseActivity
from app.models.enums import CaseActivityType, CaseStatus, UserStatus, WorkspaceStatus
from app.models.universal_case import UniversalCase
from app.models.user import User
from app.models.workspace import Workspace


def _column_names(table_name: str) -> set[str]:
    return {column.name for column in Base.metadata.tables[table_name].columns}


def _foreign_key_targets(table_name: str, column_name: str) -> set[str]:
    column = Base.metadata.tables[table_name].c[column_name]
    return {fk.column.table.name for fk in column.foreign_keys}


def test_case_activities_columns() -> None:
    assert _column_names("case_activities") == {
        "id",
        "workspace_id",
        "case_id",
        "actor_user_id",
        "activity_type",
        "metadata",
        "message",
        "created_at",
    }


def test_case_activities_workspace_fk() -> None:
    assert _foreign_key_targets("case_activities", "workspace_id") == {"workspaces"}


def test_case_activities_case_fk() -> None:
    assert _foreign_key_targets("case_activities", "case_id") == {"universal_cases"}


def test_case_activities_actor_user_fk() -> None:
    assert _foreign_key_targets("case_activities", "actor_user_id") == {"users"}


def test_case_activities_indexes() -> None:
    indexes = Base.metadata.tables["case_activities"].indexes
    index_columns = {tuple(index.columns.keys()) for index in indexes}
    assert ("workspace_id",) in index_columns
    assert ("case_id",) in index_columns
    assert ("actor_user_id",) in index_columns


def test_case_activity_case_relationship() -> None:
    assert CaseActivity.case.property.back_populates == "activities"
    assert UniversalCase.activities.property.back_populates == "case"


def test_case_activity_workspace_relationship() -> None:
    assert CaseActivity.workspace.property.back_populates == "case_activities"
    assert Workspace.case_activities.property.back_populates == "workspace"


async def _create_workspace_case(
    db_session: AsyncSession,
) -> tuple[Workspace, UniversalCase, User]:
    suffix = uuid.uuid4().hex[:12]
    workspace = Workspace(
        name=f"Activity Workspace {suffix}",
        slug=f"activity-workspace-{suffix}",
        status=WorkspaceStatus.ACTIVE,
    )
    user = User(
        email=f"activity-user-{suffix}@example.com",
        password_hash="hashed-password",
        status=UserStatus.ACTIVE,
    )
    db_session.add_all([workspace, user])
    await db_session.flush()

    case = UniversalCase(
        workspace_id=workspace.id,
        title="Activity test case",
        status=CaseStatus.OPEN,
        created_by_user_id=user.id,
    )
    db_session.add(case)
    await db_session.flush()
    return workspace, case, user


@pytest.mark.asyncio
async def test_case_activity_can_be_created_for_workspace_and_case(
    db_session: AsyncSession,
) -> None:
    workspace, case, user = await _create_workspace_case(db_session)

    activity = CaseActivity(
        workspace_id=workspace.id,
        case_id=case.id,
        actor_user_id=user.id,
        activity_type=CaseActivityType.STATUS_CHANGED,
        message="Status changed to pending",
        activity_metadata={"from": "open", "to": "pending"},
    )
    db_session.add(activity)
    await db_session.flush()
    await db_session.refresh(activity)

    assert activity.id is not None
    assert activity.workspace_id == workspace.id
    assert activity.case_id == case.id
    assert activity.actor_user_id == user.id
    assert activity.activity_type == CaseActivityType.STATUS_CHANGED
    assert activity.message == "Status changed to pending"
    assert activity.activity_metadata == {"from": "open", "to": "pending"}


@pytest.mark.asyncio
async def test_case_activity_actor_user_id_can_be_null(
    db_session: AsyncSession,
) -> None:
    workspace, case, _user = await _create_workspace_case(db_session)

    activity = CaseActivity(
        workspace_id=workspace.id,
        case_id=case.id,
        actor_user_id=None,
        activity_type=CaseActivityType.CASE_CREATED,
    )
    db_session.add(activity)
    await db_session.flush()
    await db_session.refresh(activity)

    assert activity.actor_user_id is None


@pytest.mark.asyncio
async def test_case_activity_metadata_defaults_to_empty_dict(
    db_session: AsyncSession,
) -> None:
    workspace, case, _user = await _create_workspace_case(db_session)

    activity = CaseActivity(
        workspace_id=workspace.id,
        case_id=case.id,
        activity_type=CaseActivityType.CASE_CREATED,
    )
    db_session.add(activity)
    await db_session.flush()
    await db_session.refresh(activity)

    assert activity.activity_metadata == {}


@pytest.mark.asyncio
async def test_case_activity_message_can_be_null(
    db_session: AsyncSession,
) -> None:
    workspace, case, _user = await _create_workspace_case(db_session)

    activity = CaseActivity(
        workspace_id=workspace.id,
        case_id=case.id,
        activity_type=CaseActivityType.CASE_CREATED,
        message=None,
    )
    db_session.add(activity)
    await db_session.flush()
    await db_session.refresh(activity)

    assert activity.message is None


@pytest.mark.asyncio
async def test_case_activity_created_at_is_populated(
    db_session: AsyncSession,
) -> None:
    workspace, case, _user = await _create_workspace_case(db_session)

    activity = CaseActivity(
        workspace_id=workspace.id,
        case_id=case.id,
        activity_type=CaseActivityType.CASE_CREATED,
    )
    db_session.add(activity)
    await db_session.flush()
    await db_session.refresh(activity)

    assert activity.created_at is not None


@pytest.mark.asyncio
async def test_case_activity_type_is_required(db_session: AsyncSession) -> None:
    workspace, case, _user = await _create_workspace_case(db_session)

    activity = CaseActivity(
        workspace_id=workspace.id,
        case_id=case.id,
        activity_type=None,  # type: ignore[arg-type]
    )
    db_session.add(activity)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_deleting_universal_case_deletes_related_activities(
    db_session: AsyncSession,
) -> None:
    workspace, case, user = await _create_workspace_case(db_session)

    activity = CaseActivity(
        workspace_id=workspace.id,
        case_id=case.id,
        actor_user_id=user.id,
        activity_type=CaseActivityType.CASE_CREATED,
    )
    db_session.add(activity)
    await db_session.flush()
    activity_id = activity.id

    await db_session.delete(case)
    await db_session.flush()

    assert await db_session.get(CaseActivity, activity_id) is None
