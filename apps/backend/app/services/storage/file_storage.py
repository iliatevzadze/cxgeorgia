"""Object storage abstraction for case attachments."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from functools import lru_cache
from io import BytesIO
from typing import Protocol
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error

from app.core.config import Settings, get_settings


class StorageError(Exception):
    """Base storage backend error."""


class StorageUploadError(StorageError):
    """Raised when an object upload fails."""


class StorageDeleteError(StorageError):
    """Raised when an object delete fails."""


class FileStorage(Protocol):
    """Storage backend contract for attachment files."""

    def upload_file(
        self,
        file_bytes: bytes,
        bucket: str,
        key: str,
        content_type: str | None = None,
    ) -> None:
        """Store file bytes at the given bucket/key."""

    def delete_file(self, bucket: str, key: str) -> None:
        """Remove an object from storage."""

    def generate_presigned_upload_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        """Return a presigned URL for uploading an object."""

    def generate_presigned_download_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        """Return a presigned URL for downloading an object."""


class MemoryFileStorage:
    """In-memory storage backend for tests and local isolation."""

    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}
        self.upload_should_fail = False
        self.delete_calls: list[tuple[str, str]] = []

    def upload_file(
        self,
        file_bytes: bytes,
        bucket: str,
        key: str,
        content_type: str | None = None,
    ) -> None:
        _ = content_type
        if self.upload_should_fail:
            raise StorageUploadError("Simulated upload failure")
        self.objects[(bucket, key)] = file_bytes

    def delete_file(self, bucket: str, key: str) -> None:
        self.delete_calls.append((bucket, key))
        self.objects.pop((bucket, key), None)

    def generate_presigned_upload_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        return f"https://storage.test/upload/{bucket}/{key}?expires={expires_in}"

    def generate_presigned_download_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        return f"https://storage.test/download/{bucket}/{key}?expires={expires_in}"


class MinioFileStorage:
    """MinIO/S3-compatible storage backend."""

    def __init__(self, settings: Settings) -> None:
        endpoint = settings.storage_endpoint
        parsed = urlparse(endpoint)
        secure = parsed.scheme == "https"
        host = parsed.netloc or parsed.path
        self._client = Minio(
            host,
            access_key=settings.storage_access_key,
            secret_key=settings.storage_secret_key,
            secure=secure,
        )

    def _ensure_bucket(self, bucket: str) -> None:
        if not self._client.bucket_exists(bucket):
            self._client.make_bucket(bucket)

    def upload_file(
        self,
        file_bytes: bytes,
        bucket: str,
        key: str,
        content_type: str | None = None,
    ) -> None:
        try:
            self._ensure_bucket(bucket)
            self._client.put_object(
                bucket,
                key,
                BytesIO(file_bytes),
                length=len(file_bytes),
                content_type=content_type or "application/octet-stream",
            )
        except S3Error as exc:
            raise StorageUploadError("File upload failed") from exc

    def delete_file(self, bucket: str, key: str) -> None:
        try:
            self._client.remove_object(bucket, key)
        except S3Error as exc:
            raise StorageDeleteError("File delete failed") from exc

    def generate_presigned_upload_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        return self._client.presigned_put_object(
            bucket,
            key,
            expires=timedelta(seconds=expires_in),
        )

    def generate_presigned_download_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        return self._client.presigned_get_object(
            bucket,
            key,
            expires=timedelta(seconds=expires_in),
        )


@lru_cache
def _build_minio_storage() -> MinioFileStorage:
    return MinioFileStorage(get_settings())


def get_file_storage() -> FileStorage:
    """Return the configured file storage backend."""
    return _build_minio_storage()


async def upload_file(
    storage: FileStorage,
    file_bytes: bytes,
    bucket: str,
    key: str,
    content_type: str | None = None,
) -> None:
    await asyncio.to_thread(
        storage.upload_file,
        file_bytes,
        bucket,
        key,
        content_type,
    )


async def delete_file(storage: FileStorage, bucket: str, key: str) -> None:
    await asyncio.to_thread(storage.delete_file, bucket, key)
