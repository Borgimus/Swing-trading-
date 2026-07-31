from __future__ import annotations

import hashlib
import re
from collections import Counter
from dataclasses import replace
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from swing_trading.tc2000.models import (
    BatchEvidence,
    CandidateMode,
    CandidateRecord,
    EvidenceFile,
    ImportErrorCode,
    ImportPersistence,
    ImportPolicy,
    ImportRequest,
    ImportResult,
    ImportStatus,
    MembershipRecord,
    RawBatchStore,
    ScanKind,
    ScanUpload,
    SessionCalendar,
)
from swing_trading.tc2000.raw_store import RawStorageError

_FILENAME = re.compile(
    r"^tc2000_(?P<date>\d{4}-\d{2}-\d{2})_"
    r"(?P<kind>strength20|strength60|strength120)_"
    r"(?P<timestamp>\d{8}T\d{6}[+-]\d{4})\.txt$"
)
_SYMBOL = re.compile(r"^[A-Z][A-Z0-9]{0,9}(?:[.-][A-Z0-9]{1,4})?$")
_RESERVED_ROWS = {"SYMBOL", "SYMBOLS", "TICKER", "TICKERS"}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_NEW_YORK = ZoneInfo("America/New_York")


class BatchRejected(ValueError):
    def __init__(self, code: ImportErrorCode, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


class Tc2000Importer:
    def __init__(
        self,
        persistence: ImportPersistence,
        raw_store: RawBatchStore,
        calendar: SessionCalendar,
        policy: ImportPolicy,
    ) -> None:
        self._persistence = persistence
        self._raw_store = raw_store
        self._calendar = calendar
        self._policy = policy

    def import_batch(self, request: ImportRequest) -> ImportResult:
        if request.received_at.tzinfo is None:
            raise ValueError("received_at must be timezone-aware")
        if _SHA256.fullmatch(request.config_sha256) is None:
            return self._failure_without_persistence(
                "0" * 64,
                ImportErrorCode.INVALID_CONFIG_FINGERPRINT,
                "configuration SHA-256 fingerprint is invalid",
            )
        request = replace(
            request, uploads=tuple(sorted(request.uploads, key=lambda item: item.filename))
        )
        content_hashes = tuple(hashlib.sha256(item.content).hexdigest() for item in request.uploads)
        batch_sha256 = self._batch_hash(request.uploads, content_hashes, request.config_sha256)
        try:
            stored = self._raw_store.persist(
                batch_sha256, request.uploads, content_hashes, request.received_at
            )
        except RawStorageError as exc:
            return self._failure_without_persistence(
                batch_sha256, ImportErrorCode.RAW_STORAGE_FAILURE, str(exc)
            )

        evidence = BatchEvidence(
            batch_sha256=batch_sha256,
            config_sha256=request.config_sha256,
            expected_market_date=request.expected_market_date,
            received_at=request.received_at,
            manifest_uri=stored.manifest_uri,
            files=tuple(
                EvidenceFile(
                    file_index=index,
                    filename=upload.filename,
                    content_sha256=content_hashes[index],
                    raw_uri=stored.file_uris[index],
                )
                for index, upload in enumerate(request.uploads)
            ),
        )
        try:
            existing = self._persistence.find_by_hash(batch_sha256)
        except Exception:
            return self._failure_without_persistence(
                batch_sha256,
                ImportErrorCode.PERSISTENCE_FAILURE,
                "database unavailable while checking import replay",
            )
        if existing is not None:
            replay_status = (
                ImportStatus.ALREADY_IMPORTED
                if existing.status in {ImportStatus.ACCEPTED, ImportStatus.ALREADY_IMPORTED}
                else ImportStatus.ALREADY_REJECTED
            )
            return ImportResult(
                status=replay_status,
                batch_sha256=batch_sha256,
                batch_id=existing.batch_id,
                error_code=existing.error_code,
                detail="identical raw batch was already recorded",
                candidate_counts={},
            )

        try:
            evidence, memberships, candidates = self._validate_and_derive(request, evidence)
        except BatchRejected as rejection:
            try:
                persisted = self._persistence.record_rejected(
                    evidence, rejection.code, rejection.detail
                )
            except Exception:
                return self._failure_without_persistence(
                    batch_sha256,
                    ImportErrorCode.PERSISTENCE_FAILURE,
                    f"{rejection.code}: raw evidence preserved but rejection record failed",
                )
            return ImportResult(
                status=ImportStatus.REJECTED,
                batch_sha256=batch_sha256,
                batch_id=persisted.batch_id,
                error_code=rejection.code,
                detail=rejection.detail,
                candidate_counts={},
            )

        try:
            persisted = self._persistence.record_accepted(evidence, memberships, candidates)
        except Exception:
            return self._failure_without_persistence(
                batch_sha256,
                ImportErrorCode.PERSISTENCE_FAILURE,
                "raw evidence preserved but atomic database activation failed",
            )
        counts = Counter(candidate.mode for candidate in candidates)
        return ImportResult(
            status=ImportStatus.ACCEPTED,
            batch_sha256=batch_sha256,
            batch_id=persisted.batch_id,
            error_code=None,
            detail=None,
            candidate_counts={mode: counts[mode] for mode in CandidateMode},
        )

    def _validate_and_derive(
        self, request: ImportRequest, evidence: BatchEvidence
    ) -> tuple[BatchEvidence, tuple[MembershipRecord, ...], tuple[CandidateRecord, ...]]:
        if len(request.uploads) != 3:
            raise BatchRejected(
                ImportErrorCode.INCOMPLETE_BATCH, "exactly three files are required"
            )
        if not self._calendar.is_session(request.expected_market_date):
            raise BatchRejected(
                ImportErrorCode.NON_SESSION_MARKET_DATE,
                "expected market date is not an exchange session",
            )

        parsed_files: list[EvidenceFile] = []
        for evidence_file, upload in zip(evidence.files, request.uploads, strict=True):
            parsed_files.append(self._parse_file(evidence_file, upload.content))
        evidence = replace(evidence, files=tuple(parsed_files))

        kinds = [item.scan_kind for item in parsed_files]
        if len(set(kinds)) != 3:
            raise BatchRejected(
                ImportErrorCode.DUPLICATE_SCAN_KIND, "one file for each scan kind is required"
            )
        dates = {item.market_date for item in parsed_files}
        if len(dates) != 1:
            raise BatchRejected(
                ImportErrorCode.MIXED_MARKET_DATE, "scan filenames contain different market dates"
            )
        if dates != {request.expected_market_date}:
            raise BatchRejected(
                ImportErrorCode.UNEXPECTED_MARKET_DATE,
                "filename market date does not match the requested market date",
            )

        export_times = [item.exported_at for item in parsed_files]
        if any(value is None for value in export_times):
            raise AssertionError("parsed files must have export timestamps")
        resolved_times = [value for value in export_times if value is not None]
        earliest = min(resolved_times)
        latest = max(resolved_times)
        if latest - earliest > self._policy.max_export_skew:
            raise BatchRejected(
                ImportErrorCode.TIMESTAMP_SKEW, "scan export timestamps exceed allowed skew"
            )
        received_utc = request.received_at.astimezone(UTC)
        if latest.astimezone(UTC) - received_utc > self._policy.max_future_offset:
            raise BatchRejected(
                ImportErrorCode.FUTURE_TIMESTAMP, "scan export timestamp is in the future"
            )
        if received_utc - earliest.astimezone(UTC) > self._policy.max_batch_age:
            raise BatchRejected(ImportErrorCode.STALE_BATCH, "one or more scan files are stale")

        memberships = tuple(
            MembershipRecord(scan_kind=item.scan_kind, symbol=symbol, source_row=row)
            for item in parsed_files
            if item.scan_kind is not None
            for row, symbol in enumerate(item.symbols, start=1)
        )
        symbol_counts = Counter(record.symbol for record in memberships)
        candidates: list[CandidateRecord] = []
        for symbol in sorted(symbol_counts):
            agreement_count = symbol_counts[symbol]
            candidates.append(
                CandidateRecord(
                    mode=CandidateMode.UNION_RANKED,
                    symbol=symbol,
                    agreement_count=agreement_count,
                    execution_eligible=False,
                )
            )
            if agreement_count >= 2:
                candidates.append(
                    CandidateRecord(
                        mode=CandidateMode.AGREEMENT_2_OF_3,
                        symbol=symbol,
                        agreement_count=agreement_count,
                        execution_eligible=False,
                    )
                )
            if agreement_count == 3:
                candidates.append(
                    CandidateRecord(
                        mode=CandidateMode.INTERSECTION_3_OF_3,
                        symbol=symbol,
                        agreement_count=agreement_count,
                        execution_eligible=True,
                    )
                )
        return evidence, memberships, tuple(candidates)

    @staticmethod
    def _parse_file(evidence: EvidenceFile, content: bytes) -> EvidenceFile:
        match = _FILENAME.fullmatch(evidence.filename)
        if match is None:
            raise BatchRejected(
                ImportErrorCode.INVALID_FILENAME, f"invalid filename: {evidence.filename}"
            )
        try:
            market_date = date.fromisoformat(match.group("date"))
            exported_at = datetime.strptime(match.group("timestamp"), "%Y%m%dT%H%M%S%z")
        except ValueError as exc:
            raise BatchRejected(
                ImportErrorCode.INVALID_FILENAME, f"invalid filename date: {evidence.filename}"
            ) from exc
        new_york_time = exported_at.astimezone(_NEW_YORK)
        if (
            exported_at.utcoffset() != new_york_time.utcoffset()
            or new_york_time.date() != market_date
        ):
            raise BatchRejected(
                ImportErrorCode.INVALID_TIMEZONE_OFFSET,
                "export timestamp must use the New York offset for its market date",
            )
        try:
            decoded = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BatchRejected(
                ImportErrorCode.MALFORMED_CONTENT, "scan file is not valid UTF-8"
            ) from exc
        lines = decoded.splitlines()
        if not lines or all(not line.strip() for line in lines):
            raise BatchRejected(ImportErrorCode.EMPTY_FILE, "scan file is empty")
        symbols: list[str] = []
        for line_number, line in enumerate(lines, start=1):
            normalized = line.strip().upper()
            if (
                not normalized
                or normalized in _RESERVED_ROWS
                or _SYMBOL.fullmatch(normalized) is None
            ):
                raise BatchRejected(
                    ImportErrorCode.MALFORMED_CONTENT,
                    f"invalid symbol-only row {line_number} in {evidence.filename}",
                )
            symbols.append(normalized)
        if len(symbols) != len(set(symbols)):
            raise BatchRejected(
                ImportErrorCode.DUPLICATE_SYMBOL,
                f"duplicate symbol in {evidence.filename}",
            )
        return replace(
            evidence,
            scan_kind=ScanKind(match.group("kind")),
            market_date=market_date,
            exported_at=exported_at,
            symbols=tuple(symbols),
        )

    @staticmethod
    def _batch_hash(
        uploads: tuple[ScanUpload, ...],
        content_hashes: tuple[str, ...],
        config_sha256: str,
    ) -> str:
        digest = hashlib.sha256()
        digest.update(config_sha256.encode("ascii"))
        digest.update(b"\x00")
        for upload, content_hash in sorted(
            zip(uploads, content_hashes, strict=True),
            key=lambda pair: pair[0].filename,
        ):
            digest.update(upload.filename.encode("utf-8"))
            digest.update(b"\x00")
            digest.update(content_hash.encode("ascii"))
            digest.update(b"\x00")
        return digest.hexdigest()

    @staticmethod
    def _failure_without_persistence(
        batch_sha256: str, error_code: ImportErrorCode, detail: str
    ) -> ImportResult:
        return ImportResult(
            status=ImportStatus.REJECTED,
            batch_sha256=batch_sha256,
            batch_id=None,
            error_code=error_code,
            detail=detail,
            candidate_counts={},
        )
