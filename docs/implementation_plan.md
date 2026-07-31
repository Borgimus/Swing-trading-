# Phased Implementation Plan

Every phase ends with a focused commit and supervisor review. No later phase begins automatically.

## Phase 0: Design and governance

Deliver requirements classification, architecture, state machine, TC2000 handoff, schema, test plan, phase gates, ADRs, contribution templates, and delegation record.

Exit gate:

- Operator reviews unresolved choices and TC2000 workflow.
- Design contains no live-trading path.
- Delegated analysis is independently reviewed and logged.
- Documentation validation and secret scan pass.

## Phase 1: Safe foundation and imports

Deliver the Python 3.12 package skeleton, pinned dependency workflow, schema-validated configuration, PostgreSQL migrations, SQLite test adapter, exchange calendar, atomic TC2000 importer, raw-file storage abstraction, health/readiness API, structured logs, and fake adapters. Include the paper-only broker interface and endpoint guard, but no strategy order lifecycle.

Entry gate: Phase 0 approved.

Exit gate:

- Atomic accepted/rejected import integration tests pass.
- Exact paper endpoint allowlist rejects every alternative before network activity.
- Database failure and stale batch tests fail closed.
- CI formatting, lint, type, unit, integration, secret, and dependency checks pass.
- Initial versioned configuration values are explicitly approved or remain mode-blocking.

## Phase 2: Research engine and BACKTEST

Deliver indicator library, strength/rank replication, trend and contraction components, setup scoring, point-in-time event engine, corporate-action policy, realistic fill/cost models, dataset fingerprinting, walk-forward splits, experiment registry, and reports. No broker order mutation.

Entry gate: Phase 1 evidence accepted; point-in-time universe/data source selected.

Exit gate:

- Formula golden tests and anti-lookahead tests pass.
- Intraday breakout-day low and completed-daily-close timing are proven.
- Development, validation, and final out-of-sample boundaries are frozen.
- Sensitivity and stability reports expose every provisional definition.

## Phase 3: SHADOW

Deliver live-data ingestion, deterministic setup watch, breakout/time-normalized volume logic, full risk calculations, shadow state machine, dashboard/read models, notifications, daily/weekly reports, and anomaly review. Broker reads may support account-shaped validation, but no broker mutation occurs.

Entry gate: Operator verifies TC2000 setup and approves the active data feed/config version.

Exit gate:

- At least 20 market sessions complete with no duplicate intents, missing protection projection, or unexplained state drift.
- Every decision reconstructs from batch, config, data snapshots, rule results, and code commit.
- Shadow alternatives remain mechanically unable to create executable intents.
- Unresolved high-severity data/reconciliation/security findings are zero.

## Phase 4: PAPER_CONFIRM

Deliver Alpaca paper order adapter, stream processing, entry TTL/cancel logic, sizing/reservations, immediate protective stops, bounded missing-stop recovery, 5R partial, breakeven replacement, next-open final exit, reconciliation, startup recovery, operator approval UI, emergency new-entry block, and opt-in paper sandbox tests.

Entry gate: SHADOW gate accepted and paper credentials configured in an approved secret store.

Exit gate:

- At least 10 operator-confirmed paper trades complete the entire lifecycle.
- Every crash point is tested with open orders and positions.
- Every position is protected or in an actively managed blocked/exit state.
- Broker positions, orders, fills, account equity, and daily reports reconcile.
- No duplicate orders or unresolved high-severity security/reconciliation defects.

## Phase 5: Operations hardening

Deliver authenticated production dashboard, provider-neutral notifications, Docker Compose or systemd deployment, database backup/restore, JSON log rotation, clock monitoring, graceful shutdown, readiness/startup reconciliation, outage/missing-stop/duplicate/stale-scan/corrupt-database runbooks, and the optional import-only Windows companion if approved.

Entry gate: PAPER_CONFIRM lifecycle evidence accepted.

Exit gate:

- Restore drill, process restart, broker outage, data outage, missing-stop, duplicate-order, stale-scan, and corrupted-database drills pass.
- Windows companion, if present, is proven unable to access broker interfaces.
- Branch protection and required CI are configured on GitHub.

## Phase 6: PAPER_AUTO readiness decision

No new execution logic is added here. Generate an acceptance manifest from prior evidence and require explicit operator approval of the exact code commit and strategy configuration hash.

PAPER_AUTO remains disabled unless all are true:

- TC2000 guide is operator-verified.
- All automated tests pass.
- No unresolved high-severity security or reconciliation defects exist.
- Twenty accepted SHADOW sessions meet the stated integrity criteria.
- Ten PAPER_CONFIRM trades complete full lifecycle.
- Restart recovery is proven with open orders and positions.
- Every paper position has verified protection or an active managed exit state.
- Daily reports reconcile to Alpaca.
- Operator explicitly approves the configuration and commit.

This gate establishes operational readiness only. A separate preregistered statistical sample governs any conclusion about strategy edge.

## Change control

Any execution rule, risk limit, market-data feed, or exit policy change requires:

1. A new immutable configuration or ADR version.
2. Tests at its mathematical and lifecycle boundaries.
3. A recorded reason and reviewer.
4. Re-evaluation of affected phase evidence.
5. No automatic promotion from research or AI output.
