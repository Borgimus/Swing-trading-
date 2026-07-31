# Phase 1 Foundation

## Delivered boundary

- Python 3.12 package with fully locked dependencies.
- Frozen, strict versioned YAML configuration. It permits BACKTEST only and contains no broker host or live selector.
- SQLAlchemy models plus an Alembic migration for configuration and TC2000 audit records.
- PostgreSQL deployment boundary and explicit test-only SQLite permission.
- Immutable filesystem raw-evidence store and atomic three-file importer.
- Exact 3-of-3, 2-of-3, and union candidate derivation with only strict intersection eligible.
- Read-only broker protocol and exact Alpaca paper URL/account guard. No order method exists.
- NYSE calendar wrapper for sessions, holidays, DST, early closes, and injected unscheduled closures.
- Fail-closed liveness/readiness API and redacted JSON logging.
- Deterministic offline fakes.
- Fork-safe CI with PostgreSQL migration/import test, secret scanning, and dependency vulnerability scanning.

## Deliberately blocked

The configuration keeps the TC2000 base universe, operator verification, freshness/skew values, exposure limits, and provisional strategy thresholds unresolved. Phase 1 readiness therefore remains false. No signal evaluation, broker network connection, order submission, position management, or autonomous mode exists.

## Local validation

```bash
uv sync --frozen --all-groups
uv run swing-validate-config config/strategy-v1.yaml
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest -q
```

PostgreSQL:

```bash
docker compose up -d postgres
export DATABASE_URL='postgresql+psycopg://swing_user:local_development_only@127.0.0.1:5432/swing_trading' # pragma: allowlist secret
uv run alembic upgrade head
```

## Supervisor validation evidence

The Phase 1 review run completed with these exact results:

- `uv lock --check`: passed; 74 packages resolved from the committed lock.
- `ruff format --check .`: passed; 58 files already formatted.
- `ruff check .`: passed.
- `mypy src`: passed for 25 source files in strict mode.
- `pytest -q`: 58 passed, 1 skipped in 2.01 seconds.
- `detect-secrets-hook`: passed for every tracked file.
- `pip-audit`: passed with no known vulnerabilities in locked runtime dependencies.
- `uv build`: produced both the source distribution and wheel.
- Alembic offline PostgreSQL compilation: passed for revision `0001_phase1_foundation`.

The one skipped test is the live PostgreSQL importer integration because this review workspace
does not provide Docker or a local PostgreSQL server. The dedicated GitHub Actions PostgreSQL
job runs that migration and test after publication. Until that job passes, PostgreSQL runtime
validation remains an explicit Phase 1 acceptance dependency.
