"""Tests for Universal Case Alembic migration metadata."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def _alembic_script() -> ScriptDirectory:
    backend_root = Path(__file__).resolve().parents[1]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    return ScriptDirectory.from_config(config)


def test_0004_migration_revises_0003() -> None:
    revision = _alembic_script().get_revision("0004")
    assert revision is not None
    assert revision.down_revision == "0003"


def test_alembic_head_is_0014() -> None:
    assert _alembic_script().get_current_head() == "0014"


def test_0014_migration_revises_0013() -> None:
    revision = _alembic_script().get_revision("0014")
    assert revision is not None
    assert revision.down_revision == "0013"
