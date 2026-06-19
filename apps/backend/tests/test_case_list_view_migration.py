"""Tests for saved case list views Alembic migration metadata."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def _alembic_script() -> ScriptDirectory:
    backend_root = Path(__file__).resolve().parents[1]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    return ScriptDirectory.from_config(config)


def _migration_source(revision_id: str) -> str:
    revision = _alembic_script().get_revision(revision_id)
    assert revision is not None
    return Path(revision.path).read_text(encoding="utf-8")


def test_alembic_head_is_0015() -> None:
    assert _alembic_script().get_current_head() == "0015"


def test_0015_migration_revises_0014() -> None:
    revision = _alembic_script().get_revision("0015")
    assert revision is not None
    assert revision.down_revision == "0014"


def test_0015_migration_creates_case_list_views_table() -> None:
    source = _migration_source("0015")
    assert "op.create_table" in source
    assert '"case_list_views"' in source or "'case_list_views'" in source
    assert "uq_case_list_views_workspace_id_name" in source


def test_0015_migration_downgrade_drops_case_list_views_table() -> None:
    source = _migration_source("0015")
    assert "def downgrade" in source
    assert "op.drop_table" in source
    assert '"case_list_views"' in source or "'case_list_views'" in source
