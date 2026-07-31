from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class StrategyConfigVersion(Base):
    __tablename__ = "strategy_config_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    version: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    yaml_sha256: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    approval_status: Mapped[str] = mapped_column(String(20), nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(255))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approval_reference: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Tc2000Batch(Base):
    __tablename__ = "tc2000_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    batch_sha256: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    config_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    market_date: Mapped[date | None] = mapped_column(Date)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    earliest_exported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latest_exported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(60))
    error_detail: Mapped[str | None] = mapped_column(Text)
    raw_manifest_uri: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Tc2000File(Base):
    __tablename__ = "tc2000_files"
    __table_args__ = (UniqueConstraint("batch_id", "file_index"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    batch_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tc2000_batches.id", ondelete="CASCADE"), nullable=False
    )
    file_index: Mapped[int] = mapped_column(Integer, nullable=False)
    scan_kind: Mapped[str | None] = mapped_column(String(20))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_uri: Mapped[str] = mapped_column(Text, nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer)


class Tc2000Membership(Base):
    __tablename__ = "tc2000_memberships"
    __table_args__ = (UniqueConstraint("batch_id", "scan_kind", "symbol"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    batch_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tc2000_batches.id", ondelete="CASCADE"), nullable=False
    )
    scan_kind: Mapped[str] = mapped_column(String(20), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    source_row: Mapped[int] = mapped_column(Integer, nullable=False)
    source_rank: Mapped[int | None] = mapped_column(Integer)


class CandidateSet(Base):
    __tablename__ = "candidate_sets"
    __table_args__ = (
        UniqueConstraint("batch_id", "mode", "symbol"),
        CheckConstraint(
            "NOT execution_eligible OR mode = 'intersection_3_of_3'",
            name="candidate_execution_mode_is_strict",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    batch_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tc2000_batches.id", ondelete="CASCADE"), nullable=False
    )
    mode: Mapped[str] = mapped_column(String(30), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    agreement_count: Mapped[int] = mapped_column(Integer, nullable=False)
    composite_score: Mapped[str | None] = mapped_column(String(100))
    execution_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False)
