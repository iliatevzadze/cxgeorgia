"""Streaming file hashing helpers."""

import hashlib
from collections.abc import AsyncIterator
from typing import BinaryIO

from fastapi import UploadFile

DEFAULT_CHUNK_SIZE = 65_536


def sha256_hex_from_stream(
    stream: BinaryIO,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> tuple[str, int]:
    """Return SHA-256 hex digest and total byte count from a readable stream."""
    hasher = hashlib.sha256()
    total_bytes = 0
    stream.seek(0)
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        hasher.update(chunk)
        total_bytes += len(chunk)
    stream.seek(0)
    return hasher.hexdigest(), total_bytes


async def sha256_hex_from_upload(
    upload: UploadFile,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> tuple[bytes, str, int]:
    """Read an upload in chunks and return bytes, SHA-256 hex digest and size."""
    hasher = hashlib.sha256()
    parts: list[bytes] = []
    total_bytes = 0
    while True:
        chunk = await upload.read(chunk_size)
        if not chunk:
            break
        hasher.update(chunk)
        parts.append(chunk)
        total_bytes += len(chunk)
    return b"".join(parts), hasher.hexdigest(), total_bytes


async def sha256_hex_from_async_chunks(
    chunks: AsyncIterator[bytes],
) -> tuple[bytes, str, int]:
    """Consume async byte chunks, returning combined bytes, digest and size."""
    hasher = hashlib.sha256()
    parts: list[bytes] = []
    total_bytes = 0
    async for chunk in chunks:
        hasher.update(chunk)
        parts.append(chunk)
        total_bytes += len(chunk)
    return b"".join(parts), hasher.hexdigest(), total_bytes
