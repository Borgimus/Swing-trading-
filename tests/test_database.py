from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from swing_trading.storage.database import Database, DatabaseConfigurationError


def test_sqlite_requires_explicit_test_permission(tmp_path: Path) -> None:
    with pytest.raises(DatabaseConfigurationError, match="isolated"):
        Database.from_url(f"sqlite+pysqlite:///{tmp_path / 'blocked.db'}")


def test_unknown_database_backend_is_rejected() -> None:
    with pytest.raises(DatabaseConfigurationError, match="PostgreSQL"):
        Database.from_url("mysql://localhost/database")


def test_sqlite_ping_and_initial_migration(tmp_path: Path) -> None:
    database_path = tmp_path / "migration.db"
    url = f"sqlite+pysqlite:///{database_path}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")
    database = Database.from_url(url, allow_sqlite=True)
    try:
        assert database.ping() is True
        assert {
            "strategy_config_versions",
            "tc2000_batches",
            "tc2000_files",
            "tc2000_memberships",
            "candidate_sets",
        } <= set(inspect(database.engine).get_table_names())
    finally:
        database.dispose()
