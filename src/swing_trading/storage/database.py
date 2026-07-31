from __future__ import annotations

from dataclasses import dataclass
from sqlite3 import Connection as SQLiteConnection

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker


class DatabaseConfigurationError(ValueError):
    """Raised when a deployed database configuration violates the storage boundary."""


def _enable_sqlite_foreign_keys(
    dbapi_connection: SQLiteConnection, connection_record: object
) -> None:
    del connection_record
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


@dataclass(frozen=True, slots=True)
class Database:
    engine: Engine
    sessions: sessionmaker[Session]

    @classmethod
    def from_url(cls, url: str, *, allow_sqlite: bool = False) -> Database:
        parsed = make_url(url)
        if parsed.get_backend_name() == "sqlite" and not allow_sqlite:
            raise DatabaseConfigurationError("SQLite is allowed only in isolated development/tests")
        if parsed.get_backend_name() not in {"sqlite", "postgresql"}:
            raise DatabaseConfigurationError("database must use PostgreSQL or isolated-test SQLite")
        kwargs: dict[str, object] = {"pool_pre_ping": True}
        if parsed.get_backend_name() == "sqlite":
            kwargs["connect_args"] = {"check_same_thread": False}
        engine = create_engine(url, **kwargs)
        if parsed.get_backend_name() == "sqlite":
            event.listen(engine, "connect", _enable_sqlite_foreign_keys)
        return cls(engine=engine, sessions=sessionmaker(engine, expire_on_commit=False))

    def ping(self) -> bool:
        try:
            with self.engine.connect() as connection:
                value = connection.execute(text("SELECT 1")).scalar_one()
                return bool(value == 1)
        except Exception:
            return False

    def dispose(self) -> None:
        self.engine.dispose()
