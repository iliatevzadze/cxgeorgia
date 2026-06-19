"""Tests for saved case list view model metadata and persistence."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.schema import UniqueConstraint

import app.models  # noqa: F401 — ensure models are registered
from app.db.base import Base
from app.models.case_list_view import CaseListView
from app.models.enums import UserStatus, WorkspaceStatus
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


def test_case_list_views_columns() -> None:
    assert _column_names("case_list_views") == {
        "id",
        "workspace_id",
        "created_by_user_id",
        "name",
        "description",
        "filters",
        "sort_by",
        "sort_order",
        "page_size",
        "is_default",
        "created_at",
        "updated_at",
    }


def test_case_list_views_workspace_fk() -> None:
    assert _foreign_key_targets("case_list_views", "workspace_id") == {"workspaces"}


def test_case_list_views_created_by_user_fk() -> None:
    assert _foreign_key_targets("case_list_views", "created_by_user_id") == {"users"}


def test_case_list_views_indexes_and_unique_constraints() -> None:
    indexes = Base.metadata.tables["case_list_views"].indexes
    index_columns = {tuple(index.columns.keys()) for index in indexes}
    assert ("workspace_id",) in index_columns
    assert ("created_by_user_id",) in index_columns
    assert ("workspace_id", "is_default") in index_columns
    assert ("workspace_id", "name") in _unique_column_sets("case_list_views")


def test_workspace_case_list_views_relationship() -> None:
    assert CaseListView.workspace.property.back_populates == "case_list_views"
    assert Workspace.case_list_views.property.back_populates == "workspace"


async def _create_workspace_and_user(
    db_session: AsyncSession,
    *,
    workspace_slug_suffix: str | None = None,
) -> tuple[Workspace, User]:
    suffix = workspace_slug_suffix or uuid.uuid4().hex[:12]
    workspace = Workspace(
        name=f"View Workspace {suffix}",
        slug=f"view-workspace-{suffix}",
        status=WorkspaceStatus.ACTIVE,
    )
    user = User(
        email=f"view-user-{suffix}@example.com",
        password_hash="hashed-password",
        status=UserStatus.ACTIVE,
    )
    db_session.add_all([workspace, user])
    await db_session.flush()
    return workspace, user


@pytest.mark.asyncio
async def test_case_list_view_can_be_created_in_workspace(
    db_session: AsyncSession,
) -> None:
    workspace, user = await _create_workspace_and_user(db_session)

    view = CaseListView(
        workspace_id=workspace.id,
        created_by_user_id=user.id,
        name="Open cases",
        filters={"status": "open"},
        sort_by="created_at",
        sort_order="desc",
        page_size=25,
        is_default=True,
    )
    db_session.add(view)
    await db_session.flush()
    await db_session.refresh(view)

    assert view.id is not None
    assert view.workspace_id == workspace.id
    assert view.created_by_user_id == user.id
    assert view.name == "Open cases"
    assert view.filters == {"status": "open"}
    assert view.sort_by == "created_at"
    assert view.sort_order == "desc"
    assert view.page_size == 25
    assert view.is_default is True
    assert view.created_at is not None
    assert view.updated_at is not None


@pytest.mark.asyncio
async def test_same_name_in_same_workspace_is_rejected(
    db_session: AsyncSession,
) -> None:
    workspace, user = await _create_workspace_and_user(db_session)

    first_view = CaseListView(
        workspace_id=workspace.id,
        created_by_user_id=user.id,
        name="Shared name",
    )
    db_session.add(first_view)
    await db_session.flush()

    duplicate_view = CaseListView(
        workspace_id=workspace.id,
        created_by_user_id=user.id,
        name="Shared name",
    )
    db_session.add(duplicate_view)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_same_name_in_different_workspaces_is_allowed(
    db_session: AsyncSession,
) -> None:
    workspace_a, user_a = await _create_workspace_and_user(db_session)
    workspace_b, user_b = await _create_workspace_and_user(db_session)

    view_a = CaseListView(
        workspace_id=workspace_a.id,
        created_by_user_id=user_a.id,
        name="Shared name",
    )
    view_b = CaseListView(
        workspace_id=workspace_b.id,
        created_by_user_id=user_b.id,
        name="Shared name",
    )
    db_session.add_all([view_a, view_b])
    await db_session.flush()

    assert view_a.id is not None
    assert view_b.id is not None
    assert view_a.id != view_b.id


@pytest.mark.asyncio
async def test_deleting_workspace_removes_case_list_views(
    db_session: AsyncSession,
) -> None:
    workspace, user = await _create_workspace_and_user(db_session)

    view = CaseListView(
        workspace_id=workspace.id,
        created_by_user_id=user.id,
        name="Workspace scoped",
    )
    db_session.add(view)
    await db_session.flush()
    view_id = view.id

    await db_session.delete(workspace)
    await db_session.flush()

    assert await db_session.get(CaseListView, view_id) is None


@pytest.mark.asyncio
async def test_deleting_user_nullifies_created_by_user_id(
    db_session: AsyncSession,
) -> None:
    workspace, user = await _create_workspace_and_user(db_session)

    view = CaseListView(
        workspace_id=workspace.id,
        created_by_user_id=user.id,
        name="User scoped",
    )
    db_session.add(view)
    await db_session.flush()
    view_id = view.id

    await db_session.delete(user)
    await db_session.flush()

    refreshed = await db_session.scalar(
        select(CaseListView).where(CaseListView.id == view_id),
    )
    assert refreshed is not None
    assert refreshed.created_by_user_id is None
