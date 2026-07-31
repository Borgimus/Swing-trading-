# Requirements Audit

Status: Phase 0 design baseline. No strategy edge is assumed.

## Source-strategy facts

The supplied transcript describes these ideas without supplying reproducible thresholds:

- Long-only US-listed stock swing trades held for multiple days when exits allow.
- Daily chart governs setup and final exit; hourly chart supports inspection.
- SMA10, SMA20, SMA50, SMA200, volume, and volume EMA22 appear on both timeframes.
- Strength is sought across roughly 20, 60, and 120 daily bars, targeting the top 2% of a chosen universe.
- Candidates are above $1, move quickly, and have adequate liquidity.
- The desired pattern is an advance, then a contracting pullback near SMA10/SMA20 with rising lows, falling highs, declining volume, and a breakout.
- The breakout-day low supplies the initial stop reference.
- Planned risk cannot exceed 1% of account equity per trade.
- At 5R, sell part of the position and move the remaining stop to breakeven.
- Exit the remainder after a completed daily close below SMA10.

Performance claims are marketing claims until independently tested.

## Fixed project requirements

- Alpaca paper only. The adapter must accept only `https://paper-api.alpaca.markets`, verify the paper account, and terminate safely before any request if the boundary fails.
- There is no live endpoint, live flag, or live phase.
- TC2000 candidate input is an atomic operator upload of three exported symbol files. No API, webhook, or UI automation is claimed.
- An independently configured market-data feed recalculates every execution-critical rule. Every value retains provider, feed, timestamp, adjustment status, and payload fingerprint.
- `intersection_3_of_3` is the only initial execution-eligible candidate set. `agreement_2_of_3` and `union_ranked` remain shadow-only.
- Entries are regular-session only, use whole shares, use bounded marketable-limit or stop-limit orders, and reject duplicate exposure.
- `risk_fraction` defaults to 0.01 for paper evaluation. It may move downward through normal versioned configuration, but any upward change requires explicit review and can never exceed 0.01.
- Sizing uses reconciled paper equity, a conservative expected fill, committed open/pending risk, and buying-power, allocation, liquidity, position, and portfolio caps. A worse actual fill can reduce or reject quantity but can never increase it.
- Pyramiding is disabled. Potential add-ons are shadow records only.
- Deterministic code owns all strategy, risk, broker, and reconciliation decisions. AI has read-only access to structured records.
- PostgreSQL is the deployed store. SQLite is permitted only for isolated local tests and development.
- Broker REST snapshots and trade-update events are reconciled. Broker state controls actual order and position facts. Every discrepancy remains visible and blocks new risk.
- A filled position without a broker-acknowledged valid stop enters `RISK_BLOCKED`, blocks all new entries, alerts, and runs bounded recovery.
- The paper emergency control blocks new entries while continuing to protect, manage, and close existing positions.
- Final exit requires an official completed daily bar and executes at the next supported regular-session open by default. Near-close evaluation is shadow-only.
- BACKTEST, SHADOW, PAPER_CONFIRM, and PAPER_AUTO are separate modes with explicit promotion evidence.

## Provisional hypotheses

Every item below must live in versioned configuration and experiment records:

| Area | Provisional definition |
|---|---|
| Fast movement | `ADR20% = mean((high - low) / previous_close * 100, 20)`, minimum 5%; compare ATR20% in research |
| Liquidity | 20-day average dollar volume at least $30M; reviewed paper experiments may lower it but never below $5M |
| Trend slope | `(MA[t] / MA[t-lookback] - 1) * 100`, with positive thresholds for SMA10/20/50 and flat-to-rising treatment for SMA200 |
| MA ordering | Prefer SMA10 > SMA20 > SMA50; price above SMA50 is required |
| Consolidation | 3-15 completed daily bars |
| Structure | Two higher pivot lows and two lower pivot highs when enough bars exist; explicit pivot width remains unresolved |
| Contraction | Range width declines across the consolidation; exact estimator remains unresolved |
| MA proximity | Latest low or close within a configured percentage or ATR distance of SMA10 or SMA20 |
| Volume | Pre-breakout volume below volume EMA22 and flat-to-declining consolidation volume |
| Narrow candle | Optional true range below a configured fraction of ATR20 |
| Breakout | Highest high of the validated contraction range |
| Stop reference | Regular-session low observed only through the breakout trigger timestamp |
| Partial | First touch of actual entry + 5R; provisional fraction 25%, constrained to 20-30% |

Labels such as `strong trend` or `tight pattern` cannot substitute for stored formulas, inputs, and thresholds.

## Unresolved operator choices

| Choice | First blocked mode |
|---|---|
| Exact point-in-time US-stock universe, including ETF, ADR, SPAC, preferred, warrant, unit, and OTC treatment | BACKTEST |
| Named TC2000 base WatchList and verified top-2% rank control behavior | SHADOW |
| Market-data provider and IEX/SIP entitlement, historical coverage, and adjustment policy | BACKTEST |
| Initial slope, pivot, contraction, proximity, narrow-range, spread, chase, TTL, freshness, stop-width, exposure, and concurrency values | SHADOW |
| Whole-share 25% rounding rule for positions smaller than four shares | PAPER_CONFIRM |
| Final entry order structure after Alpaca paper sandbox verification | PAPER_CONFIRM |
| Dashboard identity provider, notification provider, and escalation recipients | PAPER_CONFIRM |
| Linux host, secret manager, backup target/RPO, clock source, and operations owner | PAPER_AUTO |
| Separate predeclared statistical sample and edge criteria | Statistical evaluation |

Interfaces may be scaffolded before these choices. Missing choices must fail closed at the first blocked mode.

## Critical hazards

- An intraday backtest cannot use the finished breakout-day low. Only observations available at the simulated trigger time are legal.
- The daily close does not exist until the official session is complete. Same-close fills for the SMA10 exit would introduce lookahead.
- A 1% planned stop risk does not cap realized gap, halt, latency, or stop-slippage loss. Reports must show planned and realized risk separately.
- TC2000 and Alpaca feeds may disagree. Candidate provenance and execution evidence must remain separate.
- The top-2% claim is not reconstructible from symbol-only files unless the base universe, ranking procedure, scan timestamp, and TC2000 settings are recorded.
- Attached-order convenience cannot weaken stop protection or exactly-once behavior.
- Passing PAPER_AUTO engineering gates does not establish economic edge.

## Phase 0 decisions

1. Use immutable, schema-validated strategy configuration snapshots. Any execution, risk, feed, or exit change requires review, a new version, tests, and a recorded reason.
2. Keep broker mutation capability confined to the deterministic execution service.
3. Persist an order intent before the external call and reuse its client order ID for every retry.
4. Treat startup reconciliation as a readiness prerequisite.
5. Preserve adjusted research series separately from unadjusted execution evidence.
6. Require operator verification of the TC2000 guide before SHADOW evidence can count toward PAPER_AUTO.
