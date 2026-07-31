from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from threading import Barrier

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import func, select

from swing_trading.storage.database import Database
from swing_trading.storage.import_repository import SqlAlchemyImportRepository
from swing_trading.storage.models import CandidateSet, Tc2000Batch, Tc2000File, Tc2000Membership
from swing_trading.tc2000.importer import Tc2000Importer
from swing_trading.tc2000.models import (
    BatchEvidence,
    CandidateMode,
    CandidateRecord,
    ImportErrorCode,
    ImportPolicy,
    ImportRequest,
    ImportResult,
    ImportStatus,
    MembershipRecord,
    PersistedBatch,
    ScanUpload,
)
from swing_trading.tc2000.raw_store import FileSystemRawBatchStore, RawStorageError
from swing_trading.testing.fakes import FakeCalendar

from .conftest import CONFIG_SHA256, MARKET_DATE, RECEIVED_AT, upload, valid_request


def test_valid_batch_is_atomic_and_derives_all_candidate_modes(
    importer: Tc2000Importer, database: Database, tmp_path: Path
) -> None:
    result = importer.import_batch(valid_request())

    assert result.status is ImportStatus.ACCEPTED
    assert result.error_code is None
    assert result.candidate_counts == {
        CandidateMode.INTERSECTION_3_OF_3: 1,
        CandidateMode.AGREEMENT_2_OF_3: 3,
        CandidateMode.UNION_RANKED: 5,
    }
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(Tc2000Batch)) == 1
        files = list(session.scalars(select(Tc2000File).order_by(Tc2000File.file_index)))
        assert len(files) == 3
        strength20 = next(row for row in files if "strength20" in row.filename)
        assert strength20.content_sha256 == hashlib.sha256(b"AAPL\nMSFT\nBRK.B\n").hexdigest()
        assert session.scalar(select(func.count()).select_from(Tc2000Membership)) == 9
        candidates = list(session.scalars(select(CandidateSet)))
    strict = {row.symbol for row in candidates if row.execution_eligible}
    assert strict == {"AAPL"}
    assert all(row.mode == "intersection_3_of_3" for row in candidates if row.execution_eligible)
    assert all(row.composite_score is None for row in candidates)

    raw_directory = tmp_path / "raw" / result.batch_sha256
    assert (raw_directory / "manifest.json").is_file()
    assert Path(strength20.raw_uri).read_bytes() == b"AAPL\nMSFT\nBRK.B\n"


def test_identical_accepted_batch_is_idempotent(
    importer: Tc2000Importer, database: Database
) -> None:
    first = importer.import_batch(valid_request())
    second = importer.import_batch(valid_request())

    assert first.status is ImportStatus.ACCEPTED
    assert second.status is ImportStatus.ALREADY_IMPORTED
    assert second.batch_id == first.batch_id
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(Tc2000Batch)) == 1


def test_upload_order_is_identity_invariant(importer: Tc2000Importer) -> None:
    request = valid_request()
    first = importer.import_batch(request)
    reversed_request = replace(request, uploads=tuple(reversed(request.uploads)))

    second = importer.import_batch(reversed_request)

    assert second.status is ImportStatus.ALREADY_IMPORTED
    assert second.batch_sha256 == first.batch_sha256
    assert second.batch_id == first.batch_id


def test_configuration_fingerprint_is_part_of_batch_identity(
    importer: Tc2000Importer, database: Database
) -> None:
    first = importer.import_batch(valid_request())
    changed_config = replace(valid_request(), config_sha256="b" * 64)

    second = importer.import_batch(changed_config)

    assert first.status is ImportStatus.ACCEPTED
    assert second.status is ImportStatus.ACCEPTED
    assert second.batch_sha256 != first.batch_sha256
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(Tc2000Batch)) == 2


def test_invalid_configuration_fingerprint_is_rejected_before_storage(
    importer: Tc2000Importer, tmp_path: Path
) -> None:
    result = importer.import_batch(replace(valid_request(), config_sha256="invalid"))

    assert result.error_code is ImportErrorCode.INVALID_CONFIG_FINGERPRINT
    assert not (tmp_path / "raw").exists()


def test_tampered_raw_evidence_blocks_replay(importer: Tc2000Importer, tmp_path: Path) -> None:
    first = importer.import_batch(valid_request())
    raw_path = tmp_path / "raw" / first.batch_sha256 / "file-00.raw"
    raw_path.write_bytes(b"TAMPERED\n")

    replay = importer.import_batch(valid_request())

    assert replay.status is ImportStatus.REJECTED
    assert replay.error_code is ImportErrorCode.RAW_STORAGE_FAILURE
    assert replay.batch_id is None


@pytest.mark.parametrize(
    ("batch_request", "error"),
    [
        (
            replace(valid_request(), uploads=valid_request().uploads[:2]),
            ImportErrorCode.INCOMPLETE_BATCH,
        ),
        (
            replace(
                valid_request(),
                uploads=(
                    upload("strength20", "AAPL\n"),
                    upload("strength20", "MSFT\n"),
                    upload("strength120", "NVDA\n"),
                ),
            ),
            ImportErrorCode.DUPLICATE_SCAN_KIND,
        ),
        (
            replace(
                valid_request(),
                uploads=(
                    upload("strength20", "\n"),
                    valid_request().uploads[1],
                    valid_request().uploads[2],
                ),
            ),
            ImportErrorCode.EMPTY_FILE,
        ),
        (
            replace(
                valid_request(),
                uploads=(
                    upload("strength20", "AAPL\naapl\n"),
                    valid_request().uploads[1],
                    valid_request().uploads[2],
                ),
            ),
            ImportErrorCode.DUPLICATE_SYMBOL,
        ),
        (
            replace(
                valid_request(),
                uploads=(
                    upload("strength20", "Symbol,Rank\nAAPL,1\n"),
                    valid_request().uploads[1],
                    valid_request().uploads[2],
                ),
            ),
            ImportErrorCode.MALFORMED_CONTENT,
        ),
        (
            replace(
                valid_request(),
                uploads=(
                    ScanUpload("tc2000_2026-07-30_strength20_20260730T160500-0400.txt", b"AAPL\n"),
                    valid_request().uploads[1],
                    valid_request().uploads[2],
                ),
            ),
            ImportErrorCode.MIXED_MARKET_DATE,
        ),
        (
            replace(
                valid_request(),
                uploads=(
                    upload("strength20", "AAPL\n", "20260731T160000-0400"),
                    upload("strength60", "AAPL\n", "20260731T160500-0400"),
                    upload("strength120", "AAPL\n", "20260731T160500-0400"),
                ),
            ),
            ImportErrorCode.TIMESTAMP_SKEW,
        ),
        (
            replace(valid_request(), received_at=RECEIVED_AT + timedelta(hours=1)),
            ImportErrorCode.STALE_BATCH,
        ),
        (
            replace(
                valid_request(),
                uploads=(
                    upload("strength20", "AAPL\n", "20260731T160500+0000"),
                    valid_request().uploads[1],
                    valid_request().uploads[2],
                ),
            ),
            ImportErrorCode.INVALID_TIMEZONE_OFFSET,
        ),
    ],
)
def test_invalid_batch_is_recorded_but_never_activates_candidates(
    importer: Tc2000Importer,
    database: Database,
    tmp_path: Path,
    batch_request: ImportRequest,
    error: ImportErrorCode,
) -> None:
    result = importer.import_batch(batch_request)

    assert result.status is ImportStatus.REJECTED
    assert result.error_code is error
    assert result.batch_id is not None
    with database.sessions() as session:
        batch = session.get(Tc2000Batch, result.batch_id)
        assert batch is not None and batch.status == "REJECTED"
        assert session.scalar(select(func.count()).select_from(CandidateSet)) == 0
    assert (tmp_path / "raw" / result.batch_sha256 / "manifest.json").is_file()


def test_rejected_batch_replay_does_not_duplicate_evidence(
    importer: Tc2000Importer, database: Database
) -> None:
    request = replace(valid_request(), uploads=valid_request().uploads[:2])

    first = importer.import_batch(request)
    second = importer.import_batch(request)

    assert first.status is ImportStatus.REJECTED
    assert second.status is ImportStatus.ALREADY_REJECTED
    assert second.batch_id == first.batch_id
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(Tc2000Batch)) == 1


def test_concurrent_identical_submissions_create_one_canonical_batch(
    importer: Tc2000Importer, database: Database
) -> None:
    barrier = Barrier(2)

    def submit() -> ImportResult:
        barrier.wait()
        return importer.import_batch(valid_request())

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: submit(), range(2)))

    assert all(result.error_code is None for result in results)
    assert len({result.batch_id for result in results}) == 1
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(Tc2000Batch)) == 1


class FailingPersistence:
    def find_by_hash(self, batch_sha256: str) -> None:
        return None

    def record_rejected(
        self, evidence: BatchEvidence, error_code: ImportErrorCode, detail: str
    ) -> PersistedBatch:
        raise RuntimeError("injected database failure")

    def record_accepted(
        self,
        evidence: BatchEvidence,
        memberships: tuple[MembershipRecord, ...],
        candidates: tuple[CandidateRecord, ...],
    ) -> PersistedBatch:
        raise RuntimeError("injected database failure")


class FailingRawStore:
    def persist(self, *args: object, **kwargs: object) -> None:
        raise RawStorageError("injected raw storage failure")


def test_database_failure_after_raw_preservation_fails_closed(tmp_path: Path) -> None:
    importer = Tc2000Importer(
        persistence=FailingPersistence(),
        raw_store=FileSystemRawBatchStore(tmp_path / "raw"),
        calendar=FakeCalendar({MARKET_DATE}),
        policy=ImportPolicy(timedelta(minutes=30), timedelta(seconds=10)),
    )

    result = importer.import_batch(valid_request())

    assert result.error_code is ImportErrorCode.PERSISTENCE_FAILURE
    assert result.batch_id is None
    assert (tmp_path / "raw" / result.batch_sha256 / "manifest.json").is_file()


def test_raw_storage_failure_never_calls_persistence() -> None:
    importer = Tc2000Importer(
        persistence=FailingPersistence(),
        raw_store=FailingRawStore(),  # type: ignore[arg-type]
        calendar=FakeCalendar({MARKET_DATE}),
        policy=ImportPolicy(timedelta(minutes=30), timedelta(seconds=10)),
    )

    result = importer.import_batch(valid_request())

    assert result.error_code is ImportErrorCode.RAW_STORAGE_FAILURE
    assert result.batch_id is None


_symbol = st.from_regex(r"[A-Z]{1,4}", fullmatch=True).filter(
    lambda value: value not in {"SYMBOL", "TICKER"}
)


@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    first=st.sets(_symbol, min_size=1, max_size=6),
    second=st.sets(_symbol, min_size=1, max_size=6),
    third=st.sets(_symbol, min_size=1, max_size=6),
)
def test_candidate_derivation_obeys_set_algebra(
    database: Database,
    tmp_path: Path,
    first: set[str],
    second: set[str],
    third: set[str],
) -> None:
    importer = Tc2000Importer(
        persistence=SqlAlchemyImportRepository(database),
        raw_store=FileSystemRawBatchStore(tmp_path / "property-raw"),
        calendar=FakeCalendar({MARKET_DATE}),
        policy=ImportPolicy(timedelta(minutes=30), timedelta(seconds=10)),
    )
    request = ImportRequest(
        uploads=(
            upload("strength20", "\n".join(sorted(first)) + "\n"),
            upload("strength60", "\n".join(sorted(second)) + "\n"),
            upload("strength120", "\n".join(sorted(third)) + "\n"),
        ),
        expected_market_date=MARKET_DATE,
        received_at=RECEIVED_AT,
        config_sha256=CONFIG_SHA256,
    )

    result = importer.import_batch(request)
    assert result.batch_id is not None
    with database.sessions() as session:
        rows = list(
            session.scalars(select(CandidateSet).where(CandidateSet.batch_id == result.batch_id))
        )
    actual = {
        mode: {row.symbol for row in rows if row.mode == mode.value} for mode in CandidateMode
    }
    counts = {
        symbol: sum(symbol in group for group in (first, second, third))
        for symbol in first | second | third
    }
    assert actual[CandidateMode.INTERSECTION_3_OF_3] == first & second & third
    assert actual[CandidateMode.AGREEMENT_2_OF_3] == {
        symbol for symbol, count in counts.items() if count >= 2
    }
    assert actual[CandidateMode.UNION_RANKED] == first | second | third
