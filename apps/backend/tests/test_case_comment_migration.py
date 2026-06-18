"""Tests for Universal Case comments Alembic migration metadata."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def _alembic_script() -> ScriptDirectory:
    backend_root = Path(__file__).resolve().parents[1]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    return ScriptDirectory.from_config(config)


def test_alembic_head_is_0005() -> None:
    assert _alembic_script().get_current_head() == "0005"


def test_0005_migration_revises_0004() -> None:
    revision = _alembic_script().get_revision("0005")
    assert revision is not None
    assert revision.down_revision == "0004"
