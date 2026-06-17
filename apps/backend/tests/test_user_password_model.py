"""Tests for User password_hash model field."""

import app.models  # noqa: F401 — ensure models are registered
from app.db.base import Base
from app.schemas.user import UserRead


def test_password_hash_exists_on_user_model() -> None:
    columns = {column.name for column in Base.metadata.tables["users"].columns}
    assert "password_hash" in columns


def test_password_hash_is_not_nullable() -> None:
    column = Base.metadata.tables["users"].c.password_hash
    assert column.nullable is False


def test_user_read_schema_excludes_password_hash() -> None:
    assert "password_hash" not in UserRead.model_fields
