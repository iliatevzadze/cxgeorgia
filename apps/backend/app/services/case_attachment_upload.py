"""Case attachment upload orchestration."""

from __future__ import annotations

import re
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_attachment import CaseAttachment
from app.schemas.case_attachment import CaseAttachmentCreate
from app.services.storage.file_storage import (
    FileStorage,
    StorageUploadError,
    delete_file,
    upload_file,
)

DUPLICATE_STORAGE_LOCATION_MESSAGE = "Storage location already exists"

_FILENAME_SAFE_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_file_name(file_name: str) -> str:
    cleaned = _FILENAME_SAFE_PATTERN.sub("_", file_name.strip())
    return cleaned or "attachment"


def build_default_storage_key(
    workspace_id: UUID,
    case_id: UUID,
    file_name: str,
) -> str:
    safe_name = sanitize_file_name(file_name)
    return (
        f"workspaces/{workspace_id}/cases/{case_id}/attachments/"
        f"{uuid4()}/{safe_name}"
    )


async def create_case_attachment_with_file(
    session: AsyncSession,
    storage: FileStorage,
    *,
    workspace_id: UUID,
    case_id: UUID,
    uploaded_by_user_id: UUID,
    file_bytes: bytes,
    file_name: str,
    content_type: str | None,
    storage_bucket: str,
    storage_key: str,
    checksum_sha256: str,
    size_bytes: int,
) -> CaseAttachment:
    """Upload file bytes to storage and persist attachment metadata."""
    metadata = CaseAttachmentCreate(
        file_name=file_name,
        content_type=content_type,
        size_bytes=size_bytes,
        storage_bucket=storage_bucket,
        storage_key=storage_key,
        checksum_sha256=checksum_sha256,
    )

    try:
        await upload_file(
            storage,
            file_bytes,
            metadata.storage_bucket,
            metadata.storage_key,
            metadata.content_type,
        )
    except StorageUploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File upload failed",
        ) from exc

    attachment = CaseAttachment(
        workspace_id=workspace_id,
        case_id=case_id,
        uploaded_by_user_id=uploaded_by_user_id,
        file_name=metadata.file_name,
        content_type=metadata.content_type,
        size_bytes=metadata.size_bytes,
        storage_bucket=metadata.storage_bucket,
        storage_key=metadata.storage_key,
        checksum_sha256=metadata.checksum_sha256,
    )
    session.add(attachment)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        try:
            await delete_file(
                storage,
                metadata.storage_bucket,
                metadata.storage_key,
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=DUPLICATE_STORAGE_LOCATION_MESSAGE,
        ) from exc

    await session.refresh(attachment)
    return attachment
