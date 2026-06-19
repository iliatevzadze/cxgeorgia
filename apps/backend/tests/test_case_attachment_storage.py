"""Tests for case attachment file storage integration."""

import hashlib
import uuid
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.case_attachment import CaseAttachment
from app.services.case_attachment_upload import create_case_attachment_with_file
from app.services.storage.file_storage import (
    MemoryFileStorage,
    get_file_storage,
)
from tests.conftest import auth_headers, response_data

pytestmark = pytest.mark.asyncio

SAMPLE_FILE = b"%PDF-1.4 case attachment content"


def _attachments_path(workspace_id: str, case_id: str) -> str:
    return f"/api/v1/workspaces/{workspace_id}/cases/{case_id}/attachments"


def _attachment_multipart(
    *,
    file_content: bytes = SAMPLE_FILE,
    file_name: str = "invoice.pdf",
    **form_fields: object,
) -> tuple[dict[str, tuple[str, bytes, str]], dict[str, str]]:
    unique = uuid.uuid4().hex
    content_type = str(form_fields.pop("content_type", "application/pdf"))
    data = {
        "file_name": file_name,
        "content_type": content_type,
        "storage_bucket": str(
            form_fields.pop("storage_bucket", "cxgeorgia-attachments"),
        ),
        "storage_key": str(
            form_fields.pop(
                "storage_key",
                f"workspaces/{unique}/cases/{unique}/{file_name}",
            ),
        ),
    }
    for key, value in form_fields.items():
        data[key] = str(value)
    files = {"file": (file_name, file_content, content_type)}
    return files, data


@pytest.fixture
def memory_storage() -> MemoryFileStorage:
    storage = MemoryFileStorage()
    app.dependency_overrides[get_file_storage] = lambda: storage
    yield storage
    app.dependency_overrides.pop(get_file_storage, None)


async def _create_workspace(
    client: AsyncClient,
    headers: dict[str, str],
    name: str,
) -> str:
    response = await client.post(
        "/api/v1/workspaces",
        json={"name": name},
        headers=headers,
    )
    assert response.status_code == 201
    return response_data(response)["workspace"]["id"]


async def _create_case(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: str,
) -> str:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": "Attachment storage case"},
        headers=headers,
    )
    assert response.status_code == 201
    return response_data(response)["id"]


async def test_file_upload_creates_storage_object_and_db_row(
    client: AsyncClient,
    memory_storage: MemoryFileStorage,
) -> None:
    headers = await auth_headers(
        client,
        f"attachment-storage-create-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Attachment Storage Create")
    case_id = await _create_case(client, headers, workspace_id)
    files, data = _attachment_multipart()

    response = await client.post(
        _attachments_path(workspace_id, case_id),
        files=files,
        data=data,
        headers=headers,
    )
    assert response.status_code == 201
    payload = response_data(response)
    assert (data["storage_bucket"], data["storage_key"]) in memory_storage.objects
    assert memory_storage.objects[(data["storage_bucket"], data["storage_key"])] == (
        SAMPLE_FILE
    )

    attachment = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        headers=headers,
    )
    assert attachment.status_code == 200
    assert payload["id"]


async def test_db_failure_triggers_storage_rollback(
    client: AsyncClient,
    memory_storage: MemoryFileStorage,
) -> None:
    headers = await auth_headers(
        client,
        f"attachment-storage-rollback-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Attachment Rollback")
    case_id = await _create_case(client, headers, workspace_id)
    files, data = _attachment_multipart()

    with patch(
        "app.services.case_attachment_upload.AsyncSession.commit",
        new_callable=AsyncMock,
        side_effect=IntegrityError("insert", {}, Exception("duplicate")),
    ):
        response = await client.post(
            _attachments_path(workspace_id, case_id),
            files=files,
            data=data,
            headers=headers,
        )

    assert response.status_code == 422
    assert (data["storage_bucket"], data["storage_key"]) not in memory_storage.objects


async def test_storage_failure_prevents_db_insert(
    client: AsyncClient,
    memory_storage: MemoryFileStorage,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"attachment-storage-fail-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Attachment Storage Fail")
    case_id = await _create_case(client, headers, workspace_id)
    files, data = _attachment_multipart()
    memory_storage.upload_should_fail = True

    response = await client.post(
        _attachments_path(workspace_id, case_id),
        files=files,
        data=data,
        headers=headers,
    )
    assert response.status_code == 503

    rows = (
        await db_session.scalars(
            select(CaseAttachment).where(
                CaseAttachment.workspace_id == UUID(workspace_id),
                CaseAttachment.case_id == UUID(case_id),
            ),
        )
    ).all()
    assert rows == []


async def test_checksum_is_generated_correctly(
    client: AsyncClient,
    memory_storage: MemoryFileStorage,
) -> None:
    headers = await auth_headers(
        client,
        f"attachment-storage-checksum-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Attachment Checksum")
    case_id = await _create_case(client, headers, workspace_id)
    files, data = _attachment_multipart(file_content=SAMPLE_FILE)

    response = await client.post(
        _attachments_path(workspace_id, case_id),
        files=files,
        data=data,
        headers=headers,
    )
    assert response.status_code == 201
    assert response_data(response)["checksum_sha256"] == hashlib.sha256(
        SAMPLE_FILE,
    ).hexdigest()


async def test_size_bytes_matches_uploaded_file_size(
    client: AsyncClient,
    memory_storage: MemoryFileStorage,
) -> None:
    headers = await auth_headers(
        client,
        f"attachment-storage-size-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Attachment Size")
    case_id = await _create_case(client, headers, workspace_id)
    file_content = b"0123456789"
    files, data = _attachment_multipart(file_content=file_content)

    response = await client.post(
        _attachments_path(workspace_id, case_id),
        files=files,
        data=data,
        headers=headers,
    )
    assert response.status_code == 201
    assert response_data(response)["size_bytes"] == len(file_content)


def test_presigned_url_generation_works_with_memory_storage() -> None:
    storage = MemoryFileStorage()
    upload_url = storage.generate_presigned_upload_url(
        "test-bucket",
        "path/file.pdf",
        expires_in=1800,
    )
    download_url = storage.generate_presigned_download_url(
        "test-bucket",
        "path/file.pdf",
        expires_in=1800,
    )
    assert upload_url.endswith("expires=1800")
    assert download_url.endswith("expires=1800")


async def test_create_case_attachment_with_file_unit_rollback(
    db_session: AsyncSession,
) -> None:
    from app.models.enums import CaseStatus, UserStatus, WorkspaceStatus
    from app.models.universal_case import UniversalCase
    from app.models.user import User
    from app.models.workspace import Workspace

    storage = MemoryFileStorage()
    workspace = Workspace(
        name="Storage Unit Workspace",
        slug=f"storage-unit-{uuid.uuid4().hex[:12]}",
        status=WorkspaceStatus.ACTIVE,
    )
    user = User(
        email=f"storage-unit-{uuid.uuid4()}@example.com",
        password_hash="hashed-password",
        status=UserStatus.ACTIVE,
    )
    db_session.add_all([workspace, user])
    await db_session.flush()
    case = UniversalCase(
        workspace_id=workspace.id,
        title="Storage unit case",
        status=CaseStatus.OPEN,
        created_by_user_id=user.id,
    )
    db_session.add(case)
    await db_session.flush()

    bucket = "unit-bucket"
    key = f"unit/{uuid.uuid4()}.bin"

    with patch.object(
        db_session,
        "commit",
        new_callable=AsyncMock,
        side_effect=IntegrityError("insert", {}, Exception("duplicate")),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await create_case_attachment_with_file(
                db_session,
                storage,
                workspace_id=workspace.id,
                case_id=case.id,
                uploaded_by_user_id=user.id,
                file_bytes=SAMPLE_FILE,
                file_name="unit.bin",
                content_type="application/octet-stream",
                storage_bucket=bucket,
                storage_key=key,
                checksum_sha256=hashlib.sha256(SAMPLE_FILE).hexdigest(),
                size_bytes=len(SAMPLE_FILE),
            )

    assert exc_info.value.status_code == 422
    assert (bucket, key) not in storage.objects
