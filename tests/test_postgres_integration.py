from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

import pytest
from sqlalchemy import delete, func, select

from swing_trading.storage.database import Database
from swing_trading.storage.import_repository import SqlAlchemyImportRepository
from swing_trading.storage.models import CandidateSet, Tc2000Batch, Tc2000File, Tc2000Membership
from swing_trading.tc2000.importer import Tc2000Importer
from swing_trading.tc2000.models import ImportPolicy, ImportStatus
from swing_trading.tc2000.raw_store import FileSystemRawBatchStore
from swing_trading.testing.fakes import FakeCalendar

from .conftest import MARKET_DATE, valid_request


@pytest.mark.skipif(not os.environ.get("TEST_POSTGRES_URL"), reason="PostgreSQL integration only")
def test_postgres_atomic_import_and_constraints(tmp_path: Path) -> None:
    database = Database.from_url(os.environ["TEST_POSTGRES_URL"])
    try:
        with database.sessions.begin() as session:
            session.execute(delete(CandidateSet))
            session.execute(delete(Tc2000Membership))
            session.execute(delete(Tc2000File))
            session.execute(delete(Tc2000Batch))
        importer = Tc2000Importer(
            persistence=SqlAlchemyImportRepository(database),
            raw_store=FileSystemRawBatchStore(tmp_path / "postgres-raw"),
            calendar=FakeCalendar({MARKET_DATE}),
            policy=ImportPolicy(timedelta(minutes=30), timedelta(seconds=10)),
        )

        result = importer.import_batch(valid_request())

        assert result.status is ImportStatus.ACCEPTED
        with database.sessions() as session:
            assert session.scalar(select(func.count()).select_from(Tc2000Batch)) == 1
            assert session.scalar(select(func.count()).select_from(CandidateSet)) == 9
    finally:
        database.dispose()
