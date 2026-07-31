from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from swing_trading.calendars.exchange import NyseCalendar
from swing_trading.config.loader import load_config
from swing_trading.config.models import ApprovalStatus
from swing_trading.storage.database import Database
from swing_trading.storage.import_repository import SqlAlchemyImportRepository
from swing_trading.tc2000.importer import Tc2000Importer
from swing_trading.tc2000.models import ImportPolicy, ImportRequest, ScanUpload
from swing_trading.tc2000.raw_store import FileSystemRawBatchStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Atomically import three TC2000 scan files")
    parser.add_argument("--market-date", required=True)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("files", nargs=3, type=Path)
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    raw_root = os.environ.get("RAW_IMPORT_ROOT")
    if not database_url or not raw_root:
        parser.error("DATABASE_URL and RAW_IMPORT_ROOT must be configured")

    loaded = load_config(args.config)
    tc2000 = loaded.settings.tc2000
    if (
        loaded.settings.operator_approval.status is not ApprovalStatus.APPROVED
        or not tc2000.operator_guide_verified
        or tc2000.base_universe_name is None
        or tc2000.max_batch_age_minutes is None
        or tc2000.max_export_skew_seconds is None
    ):
        parser.error("versioned TC2000 configuration is incomplete or not operator-approved")

    database = Database.from_url(database_url)
    importer = Tc2000Importer(
        persistence=SqlAlchemyImportRepository(database),
        raw_store=FileSystemRawBatchStore(Path(raw_root)),
        calendar=NyseCalendar(),
        policy=ImportPolicy(
            max_batch_age=timedelta(minutes=tc2000.max_batch_age_minutes),
            max_export_skew=timedelta(seconds=tc2000.max_export_skew_seconds),
        ),
    )
    paths: list[Path] = args.files
    result = importer.import_batch(
        ImportRequest(
            uploads=tuple(ScanUpload(path.name, path.read_bytes()) for path in paths),
            expected_market_date=datetime.strptime(args.market_date, "%Y-%m-%d").date(),
            received_at=datetime.now().astimezone(),
            config_sha256=loaded.sha256,
        )
    )
    print(
        json.dumps(
            {
                "status": result.status,
                "batch_id": result.batch_id,
                "batch_sha256": result.batch_sha256,
                "error_code": result.error_code,
                "detail": result.detail,
                "candidate_counts": result.candidate_counts,
            },
            default=str,
            sort_keys=True,
        )
    )
    return 0 if result.error_code is None else 2
