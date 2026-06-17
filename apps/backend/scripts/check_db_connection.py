#!/usr/bin/env python3
"""Verify PostgreSQL connectivity via async SQLAlchemy."""

import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings


async def check_connection() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            value = result.scalar_one()
            if value != 1:
                msg = f"Unexpected query result: {value!r}"
                raise RuntimeError(msg)
    finally:
        await engine.dispose()


def main() -> None:
    try:
        asyncio.run(check_connection())
    except Exception as exc:
        print(f"Database connection failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print("Database connection successful.")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
