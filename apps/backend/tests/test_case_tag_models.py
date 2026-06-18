"""Tests for Universal Case tag model metadata and persistence."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.schema import UniqueConstraint

import app.models  # noqa: F401 — ensure models are registered
from app.db.base import Base
from app.models.case_tag import CaseTag, UniversalCaseTag
from app.models.enums import CaseStatus, UserStatus, WorkspaceStatus
from app.models.universal_case import UniversalCase
from app.models.user import User
from app.models.workspace import Workspace


def _column_names(table_name: str) -> set[str]:
    return {column.name for column in Base.metadata.tables[table_name].columns}


def _foreign_key_targets(table_name: str, column_name: str) -> set[str]:
    column = Base.metadata.tables[table_name].c[column_name]
    return {fk.column.table.name for fk in column.foreign_keys}


def _unique_column_sets(table_name: str) -> set[tuple[str, ...]]:
    table = Base.metadata.tables[table_name]
    unique_sets: set[tuple[str, ...]] = set()
    for constraint in table.constraints:
        if isinstance(constraint, UniqueConstraint):
            unique_sets.add(tuple(column.name for column in constraint.columns))
    for index in table.indexes:
        if index.unique:
            unique_sets.add(tuple(column.name for column in index.columns))
    return unique_sets


def test_case_tags_columns() -> None:
    assert _column_names("case_tags") == {
        "id",
        "workspace_id",
        "name",
        "slug",
        "color",
        "created_at",
        "updated_at",
    }


def test_universal_case_tags_columns() -> None:
    assert _column_names("universal_case_tags") == {
        "case_id",
        "tag_id",
        "created_at",
    }


def test_case_tags_workspace_fk() -> None:
    assert _foreign_key_targets("case_tags", "workspace_id") == {"workspaces"}


def test_universal_case_tags_case_fk() -> None:
    assert _foreign_key_targets("universal_case_tags", "case_id") == {
        "universal_cases",
    }


def test_universal_case_tags_tag_fk() -> None:
    assert _foreign_key_targets("universal_case_tags", "tag_id") == {"case_tags"}


def test_case_tags_indexes_and_unique_constraints() -> None:
    indexes = Base.metadata.tables["case_tags"].indexes
    index_columns = {tuple(index.columns.keys()) for index in indexes}
    assert ("workspace_id",) in index_columns
    assert ("slug",) in index_columns
    assert ("workspace_id", "slug") in _unique_column_sets("case_tags")


def test_universal_case_tags_indexes_and_unique_constraints() -> None:
    table = Base.metadata.tables["universal_case_tags"]
    indexes = table.indexes
    index_columns = {tuple(index.columns.keys()) for index in indexes}
    assert ("case_id",) in index_columns
    assert ("tag_id",) in index_columns
    primary_key_columns = tuple(column.name for column in table.primary_key.columns)
    assert primary_key_columns == ("case_id", "tag_id")


def test_workspace_case_tags_relationship() -> None:
    assert CaseTag.workspace.property.back_populates == "case_tags"
    assert Workspace.case_tags.property.back_populates == "workspace"


def test_universal_case_tag_relationships() -> None:
    assert CaseTag.cases.property.back_populates == "tags"
    assert UniversalCase.tags.property.back_populates == "cases"


async def _create_workspace_case(
    db_session: AsyncSession,
    *,
    workspace_slug_suffix: str | None = None,
) -> tuple[Workspace, UniversalCase, User]:
    suffix = workspace_slug_suffix or uuid.uuid4().hex[:12]
    workspace = Workspace(
        name=f"Tag Workspace {suffix}",
        slug=f"tag-workspace-{suffix}",
        status=WorkspaceStatus.ACTIVE,
    )
    user = User(
        email=f"tag-user-{suffix}@example.com",
        password_hash="hashed-password",
        status=UserStatus.ACTIVE,
    )
    db_session.add_all([workspace, user])
    await db_session.flush()

    case = UniversalCase(
        workspace_id=workspace.id,
        title="Tag test case",
        status=CaseStatus.OPEN,
        created_by_user_id=user.id,
    )
    db_session.add(case)
    await db_session.flush()
    return workspace, case, user


@pytest.mark.asyncio
async def test_case_tag_can_be_created_in_workspace(
    db_session: AsyncSession,
) -> None:
    workspace, _case, _user = await _create_workspace_case(db_session)

    tag = CaseTag(
        workspace_id=workspace.id,
        name="Urgent",
        slug="urgent",
        color="#ff0000",
    )
    db_session.add(tag)
    await db_session.flush()
    await db_session.refresh(tag)

    assert tag.id is not None
    assert tag.workspace_id == workspace.id
    assert tag.name == "Urgent"
    assert tag.slug == "urgent"
    assert tag.color == "#ff0000"
    assert tag.created_at is not None
    assert tag.updated_at is not None


@pytest.mark.asyncio
async def test_same_slug_in_same_workspace_is_rejected(
    db_session: AsyncSession,
) -> None:
    workspace, _case, _user = await _create_workspace_case(db_session)

    first_tag = CaseTag(
        workspace_id=workspace.id,
        name="Billing",
        slug="billing",
    )
    db_session.add(first_tag)
    await db_session.flush()

    duplicate_tag = CaseTag(
        workspace_id=workspace.id,
        name="Billing duplicate",
        slug="billing",
    )
    db_session.add(duplicate_tag)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_same_slug_in_different_workspaces_is_allowed(
    db_session: AsyncSession,
) -> None:
    workspace_a, _case_a, _user_a = await _create_workspace_case(db_session)
    workspace_b, _case_b, _user_b = await _create_workspace_case(db_session)

    tag_a = CaseTag(
        workspace_id=workspace_a.id,
        name="Shared slug",
        slug="shared-slug",
    )
    tag_b = CaseTag(
        workspace_id=workspace_b.id,
        name="Shared slug",
        slug="shared-slug",
    )
    db_session.add_all([tag_a, tag_b])
    await db_session.flush()

    assert tag_a.id is not None
    assert tag_b.id is not None
    assert tag_a.id != tag_b.id


async def _attach_tag_to_case(
    db_session: AsyncSession,
    *,
    case: UniversalCase,
    tag: CaseTag,
) -> None:
    db_session.add(UniversalCaseTag(case_id=case.id, tag_id=tag.id))
    await db_session.flush()


@pytest.mark.asyncio
async def test_tag_can_be_attached_to_case(db_session: AsyncSession) -> None:
    workspace, case, _user = await _create_workspace_case(db_session)

    tag = CaseTag(
        workspace_id=workspace.id,
        name="VIP",
        slug="vip",
    )
    db_session.add(tag)
    await db_session.flush()

    await _attach_tag_to_case(db_session, case=case, tag=tag)

    join_rows = (
        await db_session.scalars(
            select(UniversalCaseTag).where(
                UniversalCaseTag.case_id == case.id,
                UniversalCaseTag.tag_id == tag.id,
            ),
        )
    ).all()
    assert len(join_rows) == 1
    assert join_rows[0].created_at is not None


@pytest.mark.asyncio
async def test_deleting_case_removes_join_row_but_not_tag(
    db_session: AsyncSession,
) -> None:
    workspace, case, _user = await _create_workspace_case(db_session)

    tag = CaseTag(
        workspace_id=workspace.id,
        name="Follow up",
        slug="follow-up",
    )
    db_session.add(tag)
    await db_session.flush()
    await _attach_tag_to_case(db_session, case=case, tag=tag)
    tag_id = tag.id

    await db_session.delete(case)
    await db_session.flush()

    assert await db_session.get(CaseTag, tag_id) is not None
    join_rows = (
        await db_session.scalars(
            select(UniversalCaseTag).where(UniversalCaseTag.tag_id == tag_id),
        )
    ).all()
    assert join_rows == []


@pytest.mark.asyncio
async def test_deleting_tag_removes_join_row_but_not_case(
    db_session: AsyncSession,
) -> None:
    workspace, case, _user = await _create_workspace_case(db_session)

    tag = CaseTag(
        workspace_id=workspace.id,
        name="Temporary",
        slug="temporary",
    )
    db_session.add(tag)
    await db_session.flush()
    await _attach_tag_to_case(db_session, case=case, tag=tag)
    case_id = case.id

    await db_session.delete(tag)
    await db_session.flush()

    assert await db_session.get(UniversalCase, case_id) is not None
    join_rows = (
        await db_session.scalars(
            select(UniversalCaseTag).where(UniversalCaseTag.case_id == case_id),
        )
    ).all()
    assert join_rows == []


@pytest.mark.asyncio
async def test_deleting_workspace_removes_tags(db_session: AsyncSession) -> None:
    workspace, _case, _user = await _create_workspace_case(db_session)

    tag = CaseTag(
        workspace_id=workspace.id,
        name="Workspace scoped",
        slug="workspace-scoped",
    )
    db_session.add(tag)
    await db_session.flush()
    tag_id = tag.id

    await db_session.delete(workspace)
    await db_session.flush()

    assert await db_session.get(CaseTag, tag_id) is None
