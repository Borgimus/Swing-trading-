# Relational Database Design

PostgreSQL is authoritative in deployed modes. Raw file/object payloads may live in encrypted object storage, but their immutable hashes and metadata live in PostgreSQL. SQLite is limited to isolated local tests.

## Configuration and provenance

| Table | Core fields and constraints |
|---|---|
| `strategy_config_versions` | `id PK`, semantic `version UNIQUE`, `yaml_sha256 UNIQUE`, `schema_version`, `approved_by`, `approved_at`, `approval_ref`, `created_at` |
| `market_data_snapshots` | `id PK`, `provider`, `feed`, `symbol`, `timeframe`, `source_timestamp`, `observed_at`, `adjustment`, `payload_sha256`, `object_uri`; unique provider/feed/symbol/timeframe/source timestamp/adjustment |
| `market_bars` | `snapshot_id FK`, `symbol`, `timeframe`, `bar_start`, OHLCV, `is_regular_session`, `is_final`; composite PK on snapshot/symbol/timeframe/bar start |
| `corporate_actions` | `id PK`, symbol, action type, ex/effective dates, ratio/cash amount, provider, payload hash; unique provider action identity |
| `calendar_sessions` | market date PK, open/close UTC, early-close flag, source version, unscheduled-closure status |

## TC2000 batches

| Table | Core fields and constraints |
|---|---|
| `tc2000_batches` | `id PK`, market date, export/received times, operator ID, base-universe name/count, TC2000 edition/feed, expected config hash, status, `batch_sha256 UNIQUE`, rejection code |
| `tc2000_files` | `id PK`, batch FK, scan kind CHECK in 20/60/120, filename, content SHA-256, object URI, row count; unique batch/scan kind |
| `tc2000_memberships` | batch FK, scan kind, normalized symbol, source row/rank nullable; composite PK batch/scan kind/symbol |
| `candidate_sets` | batch FK, mode, symbol, agreement count, composite score nullable, execution eligible; composite PK batch/mode/symbol; CHECK only 3-of-3 may initially be eligible |

Batch, file, membership, and derived candidate rows commit together. `accepted` is impossible unless exactly three scan kinds exist.

## Decisions and lifecycle

| Table | Core fields and constraints |
|---|---|
| `setup_evaluations` | `id PK`, batch/symbol/config references, daily/hourly snapshot references, evaluated time, result, breakout level, setup score, input hash; unique full evidence tuple |
| `indicator_values` | evaluation FK, timeframe, indicator name/version, bar timestamp, numeric value, inputs JSON; unique evaluation/timeframe/indicator/bar |
| `rule_results` | evaluation FK, component/rule name/version, required flag, pass flag, observed value, operator, threshold, reason; unique evaluation/rule |
| `trade_cases` | `id PK`, symbol, config FK, source evaluation FK, current state, aggregate version, opened/closed times; unique active case per symbol through a partial unique index |
| `state_transitions` | `id PK`, trade case FK, from/to state, event ID, `idempotency_key UNIQUE`, reason, guard-results JSON, aggregate version, occurred time; unique trade case/aggregate version |

## Risk and broker evidence

| Table | Core fields and constraints |
|---|---|
| `account_snapshots` | `id PK`, broker account fingerprint, observed time, equity, buying power, exposure, committed risk, payload hash; unique account/time |
| `risk_calculations` | `id PK`, trade case/evaluation/account snapshot FKs, risk fraction/dollars, expected entry, stop reference, risk/share, raw shares, each cap, final shares, planned notional/risk, inputs hash |
| `risk_reservations` | `id PK`, trade case FK, amount, status, version; only one active reservation per trade case |
| `order_intents` | `id PK`, trade case FK, action, `idempotency_key UNIQUE`, `client_order_id UNIQUE`, side/type/TIF, quantity/prices, status, request hash, created time |
| `broker_orders` | broker order ID PK, intent FK nullable, client order ID, parent/child IDs, status, quantities/prices, observed time, raw payload hash |
| `broker_events` | provider event ID PK or deterministic fallback key, received/source times, event type, raw payload hash, processing status |
| `fills` | broker fill ID PK, broker order FK, quantity, price, filled time, raw payload hash |
| `position_snapshots` | `id PK`, broker position identity, symbol, quantity, VWAP entry, observed time, payload hash; unique broker identity/time |
| `protective_stop_versions` | `id PK`, trade case, broker order FK, protected quantity, stop price, lifecycle status, replacement version, acknowledged time; one current acknowledged version per case |
| `one_time_actions` | trade case FK, action kind, durable status, intent FK; composite PK trade case/action kind, used for 5R exactly once |

## Operations and reporting

| Table | Core fields and constraints |
|---|---|
| `reconciliation_runs` | `id PK`, start/end times, trigger, broker snapshot hash, local projection hash, result |
| `reconciliation_incidents` | `id PK`, run/trade-case references, severity, kind, details, opened/resolved times, operator resolution; unresolved incidents are never overwritten |
| `service_events` | `id PK`, service instance, event kind, severity, timestamp, structured redacted details |
| `notifications` | `id PK`, source event, provider-neutral channel, template version, status, attempts, timestamps; no credentials |
| `daily_account_reports` | market date PK, opening/closing equity, realized/unrealized P&L, exposure, drawdown, broker reconciliation status, simulation limitations |
| `experiment_runs` | `id PK`, mode, config hash, dataset fingerprint, code commit, start/end, split label, status, metrics URI |
| `ai_reviews` | `id PK`, subject type/ID, model, prompt version, input/output hashes and URIs, timestamp, token/cost metadata; explicitly non-authoritative |

## Transaction boundaries

1. TC2000 activation is one transaction.
2. Each evaluation commits all provenance and required rule results before eligibility can be true.
3. Entry intent, risk reservation, and transition commit under portfolio/symbol locking before the broker call.
4. Broker events deduplicate before projections or transitions change.
5. Fill, stop-protection version, and transition updates use optimistic aggregate versions.
6. Reconciliation appends evidence and incidents. It never rewrites broker history to fit local expectations.

## Retention and integrity

- Database constraints enforce uniqueness in addition to application idempotency.
- Payload hashes use SHA-256 and object-store references are immutable/versioned.
- Timestamps are stored as UTC instants with the source timezone/market date retained where relevant.
- Sensitive headers, keys, tokens, and signed URLs are rejected or redacted before persistence.
- Backup/restore tests must prove schema, audit-history, and object references recover together.
