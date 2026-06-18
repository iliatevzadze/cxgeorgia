"""Tests for Universal Case comment model metadata and persistence."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import app.models  # noqa: F401 — ensure models are registered
from app.db.base import Base
from app.models.case_comment import CaseComment
from app.models.enums import CaseStatus, UserStatus, WorkspaceStatus
from app.models.universal_case import UniversalCase
from app.models.user import User
from app.models.workspace import Workspace


def _column_names(table_name: str) -> set[str]:
    return {column.name for column in Base.metadata.tables[table_name].columns}


def _foreign_key_targets(table_name: str, column_name: str) -> set[str]:
    column = Base.metadata.tables[table_name].c[column_name]
    return {fk.column.table.name for fk in column.foreign_keys}


def test_case_comments_columns() -> None:
    assert _column_names("case_comments") == {
        "id",
        "workspace_id",
        "case_id",
        "author_user_id",
        "body",
        "is_internal",
        "created_at",
        "updated_at",
    }


def test_case_comments_workspace_fk() -> None:
    assert _foreign_key_targets("case_comments", "workspace_id") == {"workspaces"}


def test_case_comments_case_fk() -> None:
    assert _foreign_key_targets("case_comments", "case_id") == {"universal_cases"}


def test_case_comments_author_user_fk() -> None:
    assert _foreign_key_targets("case_comments", "author_user_id") == {"users"}


def test_case_comments_indexes() -> None:
    indexes = Base.metadata.tables["case_comments"].indexes
    index_columns = {tuple(index.columns.keys()) for index in indexes}
    assert ("workspace_id",) in index_columns
    assert ("case_id",) in index_columns
    assert ("author_user_id",) in index_columns


def test_case_comment_case_relationship() -> None:
    assert CaseComment.case.property.back_populates == "comments"
    assert UniversalCase.comments.property.back_populates == "case"


def test_case_comment_workspace_relationship() -> None:
    assert CaseComment.workspace.property.back_populates == "case_comments"
    assert Workspace.case_comments.property.back_populates == "workspace"


async def _create_workspace_case(
    db_session: AsyncSession,
) -> tuple[Workspace, UniversalCase, User]:
    suffix = uuid.uuid4().hex[:12]
    workspace = Workspace(
        name=f"Comment Workspace {suffix}",
        slug=f"comment-workspace-{suffix}",
        status=WorkspaceStatus.ACTIVE,
    )
    user = User(
        email=f"comment-user-{suffix}@example.com",
        password_hash="hashed-password",
        status=UserStatus.ACTIVE,
    )
    db_session.add_all([workspace, user])
    await db_session.flush()

    case = UniversalCase(
        workspace_id=workspace.id,
        title="Comment test case",
        status=CaseStatus.OPEN,
        created_by_user_id=user.id,
    )
    db_session.add(case)
    await db_session.flush()
    return workspace, case, user


@pytest.mark.asyncio
async def test_case_comment_can_be_created_for_workspace_and_case(
    db_session: AsyncSession,
) -> None:
    workspace, case, user = await _create_workspace_case(db_session)

    comment = CaseComment(
        workspace_id=workspace.id,
        case_id=case.id,
        author_user_id=user.id,
        body="Customer called back.",
    )
    db_session.add(comment)
    await db_session.flush()
    await db_session.refresh(comment)

    assert comment.id is not None
    assert comment.workspace_id == workspace.id
    assert comment.case_id == case.id
    assert comment.author_user_id == user.id
    assert comment.body == "Customer called back."


@pytest.mark.asyncio
async def test_case_comment_body_is_required(db_session: AsyncSession) -> None:
    workspace, case, _user = await _create_workspace_case(db_session)

    comment = CaseComment(
        workspace_id=workspace.id,
        case_id=case.id,
        body=None,  # type: ignore[arg-type]
    )
    db_session.add(comment)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_case_comment_is_internal_defaults_to_true(
    db_session: AsyncSession,
) -> None:
    workspace, case, _user = await _create_workspace_case(db_session)

    comment = CaseComment(
        workspace_id=workspace.id,
        case_id=case.id,
        body="Internal note",
    )
    db_session.add(comment)
    await db_session.flush()
    await db_session.refresh(comment)

    assert comment.is_internal is True


@pytest.mark.asyncio
async def test_case_comment_timestamps_are_populated(
    db_session: AsyncSession,
) -> None:
    workspace, case, _user = await _create_workspace_case(db_session)

    comment = CaseComment(
        workspace_id=workspace.id,
        case_id=case.id,
        body="Timestamped note",
    )
    db_session.add(comment)
    await db_session.flush()
    await db_session.refresh(comment)

    assert comment.created_at is not None
    assert comment.updated_at is not None


@pytest.mark.asyncio
async def test_case_comment_author_user_id_can_be_null(
    db_session: AsyncSession,
) -> None:
    workspace, case, _user = await _create_workspace_case(db_session)

    comment = CaseComment(
        workspace_id=workspace.id,
        case_id=case.id,
        author_user_id=None,
        body="Anonymous note",
    )
    db_session.add(comment)
    await db_session.flush()
    await db_session.refresh(comment)

    assert comment.author_user_id is None


@pytest.mark.asyncio
async def test_deleting_universal_case_deletes_related_comments(
    db_session: AsyncSession,
) -> None:
    workspace, case, user = await _create_workspace_case(db_session)

    comment = CaseComment(
        workspace_id=workspace.id,
        case_id=case.id,
        author_user_id=user.id,
        body="Will be deleted with case",
    )
    db_session.add(comment)
    await db_session.flush()
    comment_id = comment.id

    await db_session.delete(case)
    await db_session.flush()

    assert await db_session.get(CaseComment, comment_id) is None
