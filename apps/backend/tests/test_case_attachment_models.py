"""Tests for Universal Case attachment model metadata and persistence."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.schema import UniqueConstraint

import app.models  # noqa: F401 — ensure models are registered
from app.db.base import Base
from app.models.case_attachment import CaseAttachment
from app.models.enums import CaseStatus, UserStatus, WorkspaceStatus
from app.models.universal_case import UniversalCase
from app.models.user import User
from app.models.workspace import Workspace


def _column_names(table_name: str) -> set[str]:
    return {column.name for column in Base.metadata.tables[table_name].columns}


def _foreign_key_targets(table_name: str, column_name: str) -> set[str]:
    column = Base.metadata.tables[table_name].c[column_name]
    return {fk.column.table.name for fk in column.foreign_keys}


def _index_column_sets(table_name: str) -> set[tuple[str, ...]]:
    table = Base.metadata.tables[table_name]
    return {tuple(index.columns.keys()) for index in table.indexes}


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


def test_case_attachments_columns() -> None:
    assert _column_names("case_attachments") == {
        "id",
        "workspace_id",
        "case_id",
        "uploaded_by_user_id",
        "file_name",
        "content_type",
        "size_bytes",
        "storage_bucket",
        "storage_key",
        "checksum_sha256",
        "created_at",
    }


def test_case_attachments_size_bytes_is_big_integer() -> None:
    column = Base.metadata.tables["case_attachments"].c.size_bytes
    assert column.type.__class__.__name__ == "BigInteger"


def test_case_attachments_workspace_fk() -> None:
    assert _foreign_key_targets("case_attachments", "workspace_id") == {"workspaces"}


def test_case_attachments_case_fk() -> None:
    assert _foreign_key_targets("case_attachments", "case_id") == {"universal_cases"}


def test_case_attachments_uploaded_by_user_fk() -> None:
    assert _foreign_key_targets("case_attachments", "uploaded_by_user_id") == {"users"}


def test_case_attachments_indexes_and_unique_constraints() -> None:
    index_columns = _index_column_sets("case_attachments")
    assert ("workspace_id",) in index_columns
    assert ("case_id",) in index_columns
    assert ("uploaded_by_user_id",) in index_columns
    assert ("storage_bucket", "storage_key") in _unique_column_sets(
        "case_attachments",
    )


def test_workspace_case_attachments_relationship() -> None:
    assert CaseAttachment.workspace.property.back_populates == "case_attachments"
    assert Workspace.case_attachments.property.back_populates == "workspace"


def test_universal_case_attachments_relationship() -> None:
    assert CaseAttachment.case.property.back_populates == "attachments"
    assert UniversalCase.attachments.property.back_populates == "case"


async def _create_workspace_case(
    db_session: AsyncSession,
    *,
    workspace_slug_suffix: str | None = None,
) -> tuple[Workspace, UniversalCase, User]:
    suffix = workspace_slug_suffix or uuid.uuid4().hex[:12]
    workspace = Workspace(
        name=f"Attachment Workspace {suffix}",
        slug=f"attachment-workspace-{suffix}",
        status=WorkspaceStatus.ACTIVE,
    )
    user = User(
        email=f"attachment-user-{suffix}@example.com",
        password_hash="hashed-password",
        status=UserStatus.ACTIVE,
    )
    db_session.add_all([workspace, user])
    await db_session.flush()

    case = UniversalCase(
        workspace_id=workspace.id,
        title="Attachment test case",
        status=CaseStatus.OPEN,
        created_by_user_id=user.id,
    )
    db_session.add(case)
    await db_session.flush()
    return workspace, case, user


def _attachment_kwargs(
    *,
    workspace_id: uuid.UUID,
    case_id: uuid.UUID,
    uploaded_by_user_id: uuid.UUID | None,
    storage_key: str,
) -> dict:
    return {
        "workspace_id": workspace_id,
        "case_id": case_id,
        "uploaded_by_user_id": uploaded_by_user_id,
        "file_name": "invoice.pdf",
        "content_type": "application/pdf",
        "size_bytes": 12_345,
        "storage_bucket": "cxgeorgia-attachments",
        "storage_key": storage_key,
        "checksum_sha256": "a" * 64,
    }


@pytest.mark.asyncio
async def test_case_attachment_can_be_created_for_case(
    db_session: AsyncSession,
) -> None:
    workspace, case, user = await _create_workspace_case(db_session)

    attachment = CaseAttachment(
        **_attachment_kwargs(
            workspace_id=workspace.id,
            case_id=case.id,
            uploaded_by_user_id=user.id,
            storage_key=f"workspaces/{workspace.id}/cases/{case.id}/invoice.pdf",
        ),
    )
    db_session.add(attachment)
    await db_session.flush()
    await db_session.refresh(attachment)

    assert attachment.id is not None
    assert attachment.workspace_id == workspace.id
    assert attachment.case_id == case.id
    assert attachment.file_name == "invoice.pdf"
    assert attachment.content_type == "application/pdf"
    assert attachment.size_bytes == 12_345
    assert attachment.storage_bucket == "cxgeorgia-attachments"
    assert attachment.checksum_sha256 == "a" * 64
    assert attachment.created_at is not None


@pytest.mark.asyncio
async def test_attachment_row_references_uploader(
    db_session: AsyncSession,
) -> None:
    workspace, case, user = await _create_workspace_case(db_session)

    attachment = CaseAttachment(
        **_attachment_kwargs(
            workspace_id=workspace.id,
            case_id=case.id,
            uploaded_by_user_id=user.id,
            storage_key=f"workspaces/{workspace.id}/cases/{case.id}/notes.txt",
        ),
    )
    db_session.add(attachment)
    await db_session.flush()
    await db_session.refresh(attachment, attribute_names=["uploaded_by"])

    assert attachment.uploaded_by_user_id == user.id
    assert attachment.uploaded_by is not None
    assert attachment.uploaded_by.id == user.id


@pytest.mark.asyncio
async def test_deleting_case_removes_attachment_row(
    db_session: AsyncSession,
) -> None:
    workspace, case, user = await _create_workspace_case(db_session)

    attachment = CaseAttachment(
        **_attachment_kwargs(
            workspace_id=workspace.id,
            case_id=case.id,
            uploaded_by_user_id=user.id,
            storage_key=f"workspaces/{workspace.id}/cases/{case.id}/delete-me.png",
        ),
    )
    db_session.add(attachment)
    await db_session.flush()
    attachment_id = attachment.id

    await db_session.delete(case)
    await db_session.flush()

    assert await db_session.get(CaseAttachment, attachment_id) is None


@pytest.mark.asyncio
async def test_deleting_workspace_removes_attachment_row(
    db_session: AsyncSession,
) -> None:
    workspace, case, user = await _create_workspace_case(db_session)

    attachment = CaseAttachment(
        **_attachment_kwargs(
            workspace_id=workspace.id,
            case_id=case.id,
            uploaded_by_user_id=user.id,
            storage_key=f"workspaces/{workspace.id}/cases/{case.id}/workspace-delete.pdf",
        ),
    )
    db_session.add(attachment)
    await db_session.flush()
    attachment_id = attachment.id

    await db_session.delete(workspace)
    await db_session.flush()

    assert await db_session.get(CaseAttachment, attachment_id) is None
    assert await db_session.get(UniversalCase, case.id) is None


@pytest.mark.asyncio
async def test_deleting_uploader_sets_uploaded_by_user_id_to_null(
    db_session: AsyncSession,
) -> None:
    workspace, case, user = await _create_workspace_case(db_session)

    attachment = CaseAttachment(
        **_attachment_kwargs(
            workspace_id=workspace.id,
            case_id=case.id,
            uploaded_by_user_id=user.id,
            storage_key=f"workspaces/{workspace.id}/cases/{case.id}/uploader-delete.pdf",
        ),
    )
    db_session.add(attachment)
    await db_session.flush()
    attachment_id = attachment.id
    case_id = case.id

    await db_session.delete(user)
    await db_session.flush()
    db_session.expire(attachment)

    persisted_attachment = await db_session.get(CaseAttachment, attachment_id)
    assert persisted_attachment is not None
    assert persisted_attachment.uploaded_by_user_id is None
    assert await db_session.get(UniversalCase, case_id) is not None


@pytest.mark.asyncio
async def test_duplicate_storage_bucket_and_storage_key_is_rejected(
    db_session: AsyncSession,
) -> None:
    workspace, case, user = await _create_workspace_case(db_session)
    storage_key = f"workspaces/{workspace.id}/cases/{case.id}/duplicate.bin"

    first_attachment = CaseAttachment(
        **_attachment_kwargs(
            workspace_id=workspace.id,
            case_id=case.id,
            uploaded_by_user_id=user.id,
            storage_key=storage_key,
        ),
    )
    db_session.add(first_attachment)
    await db_session.flush()

    duplicate_attachment = CaseAttachment(
        **_attachment_kwargs(
            workspace_id=workspace.id,
            case_id=case.id,
            uploaded_by_user_id=user.id,
            storage_key=storage_key,
        ),
    )
    db_session.add(duplicate_attachment)

    with pytest.raises(IntegrityError):
        await db_session.flush()
