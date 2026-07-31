from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from swing_trading.storage.database import Database
from swing_trading.storage.models import (
    CandidateSet,
    Tc2000Batch,
    Tc2000File,
    Tc2000Membership,
)
from swing_trading.tc2000.models import (
    BatchEvidence,
    CandidateRecord,
    ExistingBatch,
    ImportErrorCode,
    ImportStatus,
    MembershipRecord,
    PersistedBatch,
)


class SqlAlchemyImportRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def find_by_hash(self, batch_sha256: str) -> ExistingBatch | None:
        with self._database.sessions() as session:
            batch = session.scalar(
                select(Tc2000Batch).where(Tc2000Batch.batch_sha256 == batch_sha256)
            )
            if batch is None:
                return None
            error_code = ImportErrorCode(batch.error_code) if batch.error_code else None
            return ExistingBatch(
                batch_id=batch.id,
                status=ImportStatus(batch.status),
                error_code=error_code,
            )

    def record_rejected(
        self,
        evidence: BatchEvidence,
        error_code: ImportErrorCode,
        detail: str,
    ) -> PersistedBatch:
        batch_id = str(uuid4())
        try:
            with self._database.sessions.begin() as session:
                session.add(
                    self._batch_model(
                        batch_id=batch_id,
                        evidence=evidence,
                        status=ImportStatus.REJECTED,
                        error_code=error_code,
                        detail=detail,
                    )
                )
                session.add_all(self._file_models(batch_id, evidence))
        except IntegrityError:
            existing = self.find_by_hash(evidence.batch_sha256)
            if existing is None:
                raise
            return PersistedBatch(batch_id=existing.batch_id)
        return PersistedBatch(batch_id=batch_id)

    def record_accepted(
        self,
        evidence: BatchEvidence,
        memberships: tuple[MembershipRecord, ...],
        candidates: tuple[CandidateRecord, ...],
    ) -> PersistedBatch:
        batch_id = str(uuid4())
        try:
            with self._database.sessions.begin() as session:
                session.add(
                    self._batch_model(
                        batch_id=batch_id,
                        evidence=evidence,
                        status=ImportStatus.ACCEPTED,
                        error_code=None,
                        detail=None,
                    )
                )
                session.add_all(self._file_models(batch_id, evidence))
                session.add_all(
                    Tc2000Membership(
                        id=str(uuid4()),
                        batch_id=batch_id,
                        scan_kind=record.scan_kind.value,
                        symbol=record.symbol,
                        source_row=record.source_row,
                        source_rank=None,
                    )
                    for record in memberships
                )
                session.add_all(
                    CandidateSet(
                        id=str(uuid4()),
                        batch_id=batch_id,
                        mode=record.mode.value,
                        symbol=record.symbol,
                        agreement_count=record.agreement_count,
                        composite_score=None,
                        execution_eligible=record.execution_eligible,
                    )
                    for record in candidates
                )
        except IntegrityError:
            existing = self.find_by_hash(evidence.batch_sha256)
            if existing is None:
                raise
            return PersistedBatch(batch_id=existing.batch_id)
        return PersistedBatch(batch_id=batch_id)

    @staticmethod
    def _batch_model(
        *,
        batch_id: str,
        evidence: BatchEvidence,
        status: ImportStatus,
        error_code: ImportErrorCode | None,
        detail: str | None,
    ) -> Tc2000Batch:
        export_times = [item.exported_at for item in evidence.files if item.exported_at]
        return Tc2000Batch(
            id=batch_id,
            batch_sha256=evidence.batch_sha256,
            config_sha256=evidence.config_sha256,
            market_date=evidence.expected_market_date,
            received_at=evidence.received_at,
            earliest_exported_at=min(export_times) if export_times else None,
            latest_exported_at=max(export_times) if export_times else None,
            status=status.value,
            error_code=error_code.value if error_code else None,
            error_detail=detail,
            raw_manifest_uri=evidence.manifest_uri,
            created_at=datetime.now(UTC),
        )

    @staticmethod
    def _file_models(batch_id: str, evidence: BatchEvidence) -> list[Tc2000File]:
        return [
            Tc2000File(
                id=str(uuid4()),
                batch_id=batch_id,
                file_index=item.file_index,
                scan_kind=item.scan_kind.value if item.scan_kind else None,
                filename=item.filename,
                content_sha256=item.content_sha256,
                raw_uri=item.raw_uri,
                row_count=len(item.symbols) if item.symbols else None,
            )
            for item in evidence.files
        ]

    def active_candidates(self, batch_id: str) -> list[CandidateSet]:
        with self._database.sessions() as session:
            return list(
                session.scalars(
                    select(CandidateSet)
                    .join(Tc2000Batch, CandidateSet.batch_id == Tc2000Batch.id)
                    .where(
                        CandidateSet.batch_id == batch_id,
                        Tc2000Batch.status == ImportStatus.ACCEPTED.value,
                    )
                    .order_by(CandidateSet.mode, CandidateSet.symbol)
                )
            )
