"""Create Phase 1 configuration and TC2000 import tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_phase1_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "strategy_config_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("version", sa.String(100), nullable=False, unique=True),
        sa.Column("yaml_sha256", sa.String(64), nullable=False, unique=True),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("approval_status", sa.String(20), nullable=False),
        sa.Column("approved_by", sa.String(255)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("approval_reference", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "tc2000_batches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("batch_sha256", sa.String(64), nullable=False, unique=True),
        sa.Column("config_sha256", sa.String(64), nullable=False),
        sa.Column("market_date", sa.Date()),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("earliest_exported_at", sa.DateTime(timezone=True)),
        sa.Column("latest_exported_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("error_code", sa.String(60)),
        sa.Column("error_detail", sa.Text()),
        sa.Column("raw_manifest_uri", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "tc2000_files",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "batch_id",
            sa.String(36),
            sa.ForeignKey("tc2000_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_index", sa.Integer(), nullable=False),
        sa.Column("scan_kind", sa.String(20)),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("raw_uri", sa.Text(), nullable=False),
        sa.Column("row_count", sa.Integer()),
        sa.UniqueConstraint("batch_id", "file_index"),
    )
    op.create_table(
        "tc2000_memberships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "batch_id",
            sa.String(36),
            sa.ForeignKey("tc2000_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scan_kind", sa.String(20), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("source_row", sa.Integer(), nullable=False),
        sa.Column("source_rank", sa.Integer()),
        sa.UniqueConstraint("batch_id", "scan_kind", "symbol"),
    )
    op.create_table(
        "candidate_sets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "batch_id",
            sa.String(36),
            sa.ForeignKey("tc2000_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("mode", sa.String(30), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("agreement_count", sa.Integer(), nullable=False),
        sa.Column("composite_score", sa.String(100)),
        sa.Column("execution_eligible", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "NOT execution_eligible OR mode = 'intersection_3_of_3'",
            name="candidate_execution_mode_is_strict",
        ),
        sa.UniqueConstraint("batch_id", "mode", "symbol"),
    )


def downgrade() -> None:
    op.drop_table("candidate_sets")
    op.drop_table("tc2000_memberships")
    op.drop_table("tc2000_files")
    op.drop_table("tc2000_batches")
    op.drop_table("strategy_config_versions")
