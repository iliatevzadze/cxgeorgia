"""Tests for Universal Case SLA Alembic migration metadata."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def _alembic_script() -> ScriptDirectory:
    backend_root = Path(__file__).resolve().parents[1]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    return ScriptDirectory.from_config(config)


def test_0010_migration_revises_0009() -> None:
    revision = _alembic_script().get_revision("0010")
    assert revision is not None
    assert revision.down_revision == "0009"
