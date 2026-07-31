from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Protocol


class ScanKind(StrEnum):
    STRENGTH20 = "strength20"
    STRENGTH60 = "strength60"
    STRENGTH120 = "strength120"


class CandidateMode(StrEnum):
    INTERSECTION_3_OF_3 = "intersection_3_of_3"
    AGREEMENT_2_OF_3 = "agreement_2_of_3"
    UNION_RANKED = "union_ranked"


class ImportStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    ALREADY_IMPORTED = "ALREADY_IMPORTED"
    ALREADY_REJECTED = "ALREADY_REJECTED"


class ImportErrorCode(StrEnum):
    INCOMPLETE_BATCH = "INCOMPLETE_BATCH"
    INVALID_FILENAME = "INVALID_FILENAME"
    DUPLICATE_SCAN_KIND = "DUPLICATE_SCAN_KIND"
    EMPTY_FILE = "EMPTY_FILE"
    MALFORMED_CONTENT = "MALFORMED_CONTENT"
    DUPLICATE_SYMBOL = "DUPLICATE_SYMBOL"
    MIXED_MARKET_DATE = "MIXED_MARKET_DATE"
    UNEXPECTED_MARKET_DATE = "UNEXPECTED_MARKET_DATE"
    NON_SESSION_MARKET_DATE = "NON_SESSION_MARKET_DATE"
    TIMESTAMP_SKEW = "TIMESTAMP_SKEW"
    STALE_BATCH = "STALE_BATCH"
    FUTURE_TIMESTAMP = "FUTURE_TIMESTAMP"
    INVALID_TIMEZONE_OFFSET = "INVALID_TIMEZONE_OFFSET"
    RAW_STORAGE_FAILURE = "RAW_STORAGE_FAILURE"
    PERSISTENCE_FAILURE = "PERSISTENCE_FAILURE"
    INVALID_CONFIG_FINGERPRINT = "INVALID_CONFIG_FINGERPRINT"


@dataclass(frozen=True, slots=True)
class ScanUpload:
    filename: str
    content: bytes


@dataclass(frozen=True, slots=True)
class ImportRequest:
    uploads: tuple[ScanUpload, ...]
    expected_market_date: date
    received_at: datetime
    config_sha256: str


@dataclass(frozen=True, slots=True)
class ImportPolicy:
    max_batch_age: timedelta
    max_export_skew: timedelta
    max_future_offset: timedelta = timedelta(seconds=60)


@dataclass(frozen=True, slots=True)
class EvidenceFile:
    file_index: int
    filename: str
    content_sha256: str
    raw_uri: str
    scan_kind: ScanKind | None = None
    market_date: date | None = None
    exported_at: datetime | None = None
    symbols: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BatchEvidence:
    batch_sha256: str
    config_sha256: str
    expected_market_date: date
    received_at: datetime
    manifest_uri: str
    files: tuple[EvidenceFile, ...]


@dataclass(frozen=True, slots=True)
class MembershipRecord:
    scan_kind: ScanKind
    symbol: str
    source_row: int


@dataclass(frozen=True, slots=True)
class CandidateRecord:
    mode: CandidateMode
    symbol: str
    agreement_count: int
    execution_eligible: bool


@dataclass(frozen=True, slots=True)
class ExistingBatch:
    batch_id: str
    status: ImportStatus
    error_code: ImportErrorCode | None


@dataclass(frozen=True, slots=True)
class PersistedBatch:
    batch_id: str


@dataclass(frozen=True, slots=True)
class StoredRawBatch:
    manifest_uri: str
    file_uris: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ImportResult:
    status: ImportStatus
    batch_sha256: str
    batch_id: str | None
    error_code: ImportErrorCode | None
    detail: str | None
    candidate_counts: dict[CandidateMode, int]


class SessionCalendar(Protocol):
    def is_session(self, market_date: date) -> bool: ...


class RawBatchStore(Protocol):
    def persist(
        self,
        batch_sha256: str,
        uploads: tuple[ScanUpload, ...],
        content_hashes: tuple[str, ...],
        received_at: datetime,
    ) -> StoredRawBatch: ...


class ImportPersistence(Protocol):
    def find_by_hash(self, batch_sha256: str) -> ExistingBatch | None: ...

    def record_rejected(
        self,
        evidence: BatchEvidence,
        error_code: ImportErrorCode,
        detail: str,
    ) -> PersistedBatch: ...

    def record_accepted(
        self,
        evidence: BatchEvidence,
        memberships: tuple[MembershipRecord, ...],
        candidates: tuple[CandidateRecord, ...],
    ) -> PersistedBatch: ...
