"""Tests for Universal Case attachment API."""

import hashlib
import uuid
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.case_attachment import CaseAttachment
from app.models.enums import CaseStatus
from app.models.universal_case import UniversalCase
from app.services.storage.file_storage import MemoryFileStorage, get_file_storage
from tests.conftest import auth_headers, response_data

pytestmark = pytest.mark.asyncio

SAMPLE_FILE = b"%PDF-1.4 attachment api test"


@pytest.fixture(autouse=True)
def memory_storage() -> MemoryFileStorage:
    storage = MemoryFileStorage()
    app.dependency_overrides[get_file_storage] = lambda: storage
    yield storage
    app.dependency_overrides.pop(get_file_storage, None)


def _attachments_path(workspace_id: str, case_id: str) -> str:
    return f"/api/v1/workspaces/{workspace_id}/cases/{case_id}/attachments"


def _attachment_detail_path(
    workspace_id: str,
    case_id: str,
    attachment_id: str,
) -> str:
    return f"{_attachments_path(workspace_id, case_id)}/{attachment_id}"


def _attachment_multipart(
    *,
    file_content: bytes = SAMPLE_FILE,
    file_name: str = "invoice.pdf",
    storage_key: str | None = None,
    **overrides: object,
) -> tuple[dict[str, tuple[str, bytes, str]], dict[str, str]]:
    unique = uuid.uuid4().hex
    content_type = str(overrides.pop("content_type", "application/pdf"))
    data = {
        "file_name": str(overrides.pop("file_name", file_name)),
        "content_type": content_type,
        "storage_bucket": str(overrides.pop("storage_bucket", "cxgeorgia-attachments")),
        "storage_key": str(
            overrides.pop(
                "storage_key",
                storage_key or f"workspaces/{unique}/cases/{unique}/{file_name}",
            ),
        ),
    }
    if "checksum_sha256" in overrides:
        data["checksum_sha256"] = str(overrides.pop("checksum_sha256"))
    for key, value in overrides.items():
        data[key] = str(value)
    files = {
        "file": (data["file_name"], file_content, content_type),
    }
    return files, data


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
    *,
    title: str = "Attachment test case",
) -> str:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/cases",
        json={"title": title},
        headers=headers,
    )
    assert response.status_code == 201
    return response_data(response)["id"]


async def _create_attachment(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: str,
    case_id: str,
    *,
    file_content: bytes = SAMPLE_FILE,
    **form_fields: object,
) -> dict:
    files, data = _attachment_multipart(file_content=file_content, **form_fields)
    response = await client.post(
        _attachments_path(workspace_id, case_id),
        files=files,
        data=data,
        headers=headers,
    )
    return response


async def test_create_attachment_as_workspace_member(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"attachment-create-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Attachment Create")
    case_id = await _create_case(client, headers, workspace_id)
    files, data = _attachment_multipart()

    response = await client.post(
        _attachments_path(workspace_id, case_id),
        files=files,
        data=data,
        headers=headers,
    )
    assert response.status_code == 201
    result = response_data(response)
    assert result["workspace_id"] == workspace_id
    assert result["case_id"] == case_id
    assert result["file_name"] == data["file_name"]
    assert result["content_type"] == data["content_type"]
    assert result["size_bytes"] == len(SAMPLE_FILE)
    assert result["storage_bucket"] == data["storage_bucket"]
    assert result["storage_key"] == data["storage_key"]
    assert result["checksum_sha256"] == hashlib.sha256(SAMPLE_FILE).hexdigest()
    assert result["id"]
    assert result["created_at"]


async def test_create_attachment_stores_current_user_as_uploader(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"attachment-uploader-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Attachment Uploader")
    case_id = await _create_case(client, headers, workspace_id)

    me_response = await client.get("/api/v1/auth/me", headers=headers)
    user_id = response_data(me_response)["id"]

    response = await _create_attachment(client, headers, workspace_id, case_id)
    assert response.status_code == 201
    assert response_data(response)["uploaded_by_user_id"] == user_id


async def test_create_attachment_unauthenticated_returns_401(
    client: AsyncClient,
) -> None:
    response = await client.post(
        _attachments_path(str(uuid.uuid4()), str(uuid.uuid4())),
        files={"file": ("invoice.pdf", SAMPLE_FILE, "application/pdf")},
    )
    assert response.status_code == 401


async def test_list_attachments_unauthenticated_returns_401(
    client: AsyncClient,
) -> None:
    response = await client.get(
        _attachments_path(str(uuid.uuid4()), str(uuid.uuid4())),
    )
    assert response.status_code == 401


async def test_delete_attachment_unauthenticated_returns_401(
    client: AsyncClient,
) -> None:
    response = await client.delete(
        _attachment_detail_path(
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            str(uuid.uuid4()),
        ),
    )
    assert response.status_code == 401


async def test_create_attachment_non_member_returns_404(
    client: AsyncClient,
) -> None:
    owner_headers = await auth_headers(
        client,
        f"attachment-owner-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, owner_headers, "Attachment Owner")
    case_id = await _create_case(client, owner_headers, workspace_id)

    outsider_headers = await auth_headers(
        client,
        f"attachment-outsider-{uuid.uuid4()}@example.com",
    )
    response = await _create_attachment(
        client,
        outsider_headers,
        workspace_id,
        case_id,
    )
    assert response.status_code == 404


async def test_list_attachments_non_member_returns_404(client: AsyncClient) -> None:
    owner_headers = await auth_headers(
        client,
        f"attachment-list-owner-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        owner_headers,
        "Attachment List Owner",
    )
    case_id = await _create_case(client, owner_headers, workspace_id)

    outsider_headers = await auth_headers(
        client,
        f"attachment-list-outsider-{uuid.uuid4()}@example.com",
    )
    response = await client.get(
        _attachments_path(workspace_id, case_id),
        headers=outsider_headers,
    )
    assert response.status_code == 404


async def test_delete_attachment_non_member_returns_404(client: AsyncClient) -> None:
    owner_headers = await auth_headers(
        client,
        f"attachment-delete-owner-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        owner_headers,
        "Attachment Delete Owner",
    )
    case_id = await _create_case(client, owner_headers, workspace_id)
    create_response = await _create_attachment(
        client,
        owner_headers,
        workspace_id,
        case_id,
    )
    attachment_id = response_data(create_response)["id"]

    outsider_headers = await auth_headers(
        client,
        f"attachment-delete-outsider-{uuid.uuid4()}@example.com",
    )
    response = await client.delete(
        _attachment_detail_path(workspace_id, case_id, attachment_id),
        headers=outsider_headers,
    )
    assert response.status_code == 404


async def test_list_attachments_returns_only_case_attachments(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"attachment-list-case-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Attachment List Case")
    case_a = await _create_case(client, headers, workspace_id, title="Case A")
    case_b = await _create_case(client, headers, workspace_id, title="Case B")

    await _create_attachment(
        client,
        headers,
        workspace_id,
        case_a,
        storage_key=f"case-a/{uuid.uuid4()}.pdf",
    )

    await _create_attachment(
        client,
        headers,
        workspace_id,
        case_b,
        storage_key=f"case-b/{uuid.uuid4()}.pdf",
    )

    list_response = await client.get(
        _attachments_path(workspace_id, case_a),
        headers=headers,
    )
    assert list_response.status_code == 200
    items = response_data(list_response)
    assert len(items) == 1
    assert items[0]["case_id"] == case_a
    assert items[0]["file_name"] == "invoice.pdf"


async def test_list_attachments_excludes_other_workspace(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"attachment-workspace-iso-{uuid.uuid4()}@example.com",
    )
    workspace_a = await _create_workspace(client, headers, "Attachment Workspace A")
    workspace_b = await _create_workspace(client, headers, "Attachment Workspace B")
    case_a = await _create_case(client, headers, workspace_a, title="Case in A")

    await _create_attachment(
        client,
        headers,
        workspace_a,
        case_a,
        storage_key=f"ws-a/{uuid.uuid4()}.pdf",
    )

    other_case = UniversalCase(
        workspace_id=UUID(workspace_b),
        title="Case in B",
        status=CaseStatus.OPEN,
    )
    db_session.add(other_case)
    await db_session.flush()
    db_session.add(
        CaseAttachment(
            workspace_id=UUID(workspace_b),
            case_id=other_case.id,
            file_name="other.pdf",
            size_bytes=100,
            storage_bucket="cxgeorgia-attachments",
            storage_key=f"ws-b/{uuid.uuid4()}.pdf",
        )
    )
    await db_session.flush()

    list_response = await client.get(
        _attachments_path(workspace_a, case_a),
        headers=headers,
    )
    assert list_response.status_code == 200
    items = response_data(list_response)
    assert len(items) == 1
    assert items[0]["workspace_id"] == workspace_a


async def test_duplicate_storage_location_returns_422(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"attachment-dup-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Attachment Dup")
    case_a = await _create_case(client, headers, workspace_id, title="Case A")
    case_b = await _create_case(client, headers, workspace_id, title="Case B")
    storage_key = f"duplicate/{uuid.uuid4()}.pdf"
    files, data = _attachment_multipart(storage_key=storage_key)

    first = await client.post(
        _attachments_path(workspace_id, case_a),
        files=files,
        data=data,
        headers=headers,
    )
    assert first.status_code == 201

    second = await client.post(
        _attachments_path(workspace_id, case_b),
        files=files,
        data=data,
        headers=headers,
    )
    assert second.status_code == 422
    assert second.json()["detail"] == "Storage location already exists"


async def test_create_attachment_required_fields_validation(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"attachment-required-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Attachment Required")
    case_id = await _create_case(client, headers, workspace_id)

    missing_file = await client.post(
        _attachments_path(workspace_id, case_id),
        data={"file_name": "invoice.pdf"},
        headers=headers,
    )
    empty_file = await client.post(
        _attachments_path(workspace_id, case_id),
        files={"file": ("invoice.pdf", b"", "application/pdf")},
        data={"file_name": "invoice.pdf"},
        headers=headers,
    )

    assert missing_file.status_code == 422
    assert empty_file.status_code == 422


async def test_create_attachment_size_bytes_validation(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"attachment-size-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Attachment Size")
    case_id = await _create_case(client, headers, workspace_id)

    empty_file = await client.post(
        _attachments_path(workspace_id, case_id),
        files={"file": ("invoice.pdf", b"", "application/pdf")},
        data={"file_name": "invoice.pdf"},
        headers=headers,
    )

    assert empty_file.status_code == 422


async def test_delete_attachment_removes_row(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await auth_headers(
        client,
        f"attachment-delete-row-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Attachment Delete Row")
    case_id = await _create_case(client, headers, workspace_id)
    create_response = await _create_attachment(client, headers, workspace_id, case_id)
    attachment_id = UUID(response_data(create_response)["id"])

    delete_response = await client.delete(
        _attachment_detail_path(workspace_id, case_id, str(attachment_id)),
        headers=headers,
    )
    assert delete_response.status_code == 200
    assert response_data(delete_response) == {
        "id": str(attachment_id),
        "deleted": True,
    }

    assert await db_session.get(CaseAttachment, attachment_id) is None


async def test_delete_attachment_does_not_delete_case(client: AsyncClient) -> None:
    headers = await auth_headers(
        client,
        f"attachment-delete-case-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(client, headers, "Attachment Delete Case")
    case_id = await _create_case(client, headers, workspace_id)
    create_response = await _create_attachment(client, headers, workspace_id, case_id)
    attachment_id = response_data(create_response)["id"]

    delete_response = await client.delete(
        _attachment_detail_path(workspace_id, case_id, attachment_id),
        headers=headers,
    )
    assert delete_response.status_code == 200

    case_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/cases/{case_id}",
        headers=headers,
    )
    assert case_response.status_code == 200
    assert response_data(case_response)["id"] == case_id


async def test_delete_attachment_from_other_case_returns_404(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"attachment-delete-other-case-{uuid.uuid4()}@example.com",
    )
    workspace_id = await _create_workspace(
        client,
        headers,
        "Attachment Delete Other Case",
    )
    case_a = await _create_case(client, headers, workspace_id, title="Case A")
    case_b = await _create_case(client, headers, workspace_id, title="Case B")
    create_response = await _create_attachment(
        client,
        headers,
        workspace_id,
        case_b,
        storage_key=f"case-b/{uuid.uuid4()}.pdf",
    )
    attachment_id = response_data(create_response)["id"]

    response = await client.delete(
        _attachment_detail_path(workspace_id, case_a, attachment_id),
        headers=headers,
    )
    assert response.status_code == 404


async def test_delete_attachment_cross_workspace_returns_404(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"attachment-delete-cross-{uuid.uuid4()}@example.com",
    )
    workspace_a = await _create_workspace(client, headers, "Attachment Delete Cross A")
    workspace_b = await _create_workspace(client, headers, "Attachment Delete Cross B")
    case_id = await _create_case(client, headers, workspace_a)
    create_response = await _create_attachment(client, headers, workspace_a, case_id)
    attachment_id = response_data(create_response)["id"]

    response = await client.delete(
        _attachment_detail_path(workspace_b, case_id, attachment_id),
        headers=headers,
    )
    assert response.status_code == 404


async def test_create_attachment_cross_workspace_returns_404(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"attachment-cross-post-{uuid.uuid4()}@example.com",
    )
    workspace_a = await _create_workspace(client, headers, "Attachment Cross A")
    workspace_b = await _create_workspace(client, headers, "Attachment Cross B")
    case_id = await _create_case(client, headers, workspace_a)

    response = await _create_attachment(
        client,
        headers,
        workspace_b,
        case_id,
    )
    assert response.status_code == 404


async def test_list_attachments_cross_workspace_returns_404(
    client: AsyncClient,
) -> None:
    headers = await auth_headers(
        client,
        f"attachment-cross-list-{uuid.uuid4()}@example.com",
    )
    workspace_a = await _create_workspace(client, headers, "Attachment Cross List A")
    workspace_b = await _create_workspace(client, headers, "Attachment Cross List B")
    case_id = await _create_case(client, headers, workspace_a)

    response = await client.get(
        _attachments_path(workspace_b, case_id),
        headers=headers,
    )
    assert response.status_code == 404
