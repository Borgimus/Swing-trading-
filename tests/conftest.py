from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from swing_trading.storage.database import Database
from swing_trading.storage.import_repository import SqlAlchemyImportRepository
from swing_trading.storage.models import Base
from swing_trading.tc2000.importer import Tc2000Importer
from swing_trading.tc2000.models import ImportPolicy, ImportRequest, ScanUpload
from swing_trading.tc2000.raw_store import FileSystemRawBatchStore
from swing_trading.testing.fakes import FakeCalendar

MARKET_DATE = date(2026, 7, 31)
RECEIVED_AT = datetime.fromisoformat("2026-07-31T16:06:00-04:00")
CONFIG_SHA256 = "a" * 64


def upload(kind: str, symbols: str, timestamp: str = "20260731T160500-0400") -> ScanUpload:
    return ScanUpload(
        filename=f"tc2000_2026-07-31_{kind}_{timestamp}.txt",
        content=symbols.encode(),
    )


def valid_request() -> ImportRequest:
    return ImportRequest(
        uploads=(
            upload("strength20", "AAPL\nMSFT\nBRK.B\n"),
            upload("strength60", "AAPL\nMSFT\nNVDA\n"),
            upload("strength120", "AAPL\nTSLA\nNVDA\n"),
        ),
        expected_market_date=MARKET_DATE,
        received_at=RECEIVED_AT,
        config_sha256=CONFIG_SHA256,
    )


@pytest.fixture
def database(tmp_path: Path) -> Iterator[Database]:
    db = Database.from_url(f"sqlite+pysqlite:///{tmp_path / 'test.db'}", allow_sqlite=True)
    Base.metadata.create_all(db.engine)
    try:
        yield db
    finally:
        db.dispose()


@pytest.fixture
def importer(database: Database, tmp_path: Path) -> Tc2000Importer:
    return Tc2000Importer(
        persistence=SqlAlchemyImportRepository(database),
        raw_store=FileSystemRawBatchStore(tmp_path / "raw"),
        calendar=FakeCalendar({MARKET_DATE}),
        policy=ImportPolicy(
            max_batch_age=timedelta(minutes=30),
            max_export_skew=timedelta(seconds=10),
        ),
    )
