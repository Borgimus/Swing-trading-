# Test Plan

The test suite must prove deterministic behavior and failure containment. It cannot prove profitability.

## Layers

- Unit tests cover formulas, guards, parsers, calendars, and rounding with fixed inputs.
- Property tests generate price series, quantities, event orders, and failure sequences to check invariants.
- State-machine tests generate valid and invalid event paths across every durable state.
- Integration tests use fake market-data, database-fault, clock, REST-broker, and trade-stream adapters.
- Backtest-validity tests enforce event-time availability and dataset separation.
- Opt-in Alpaca sandbox tests run only with protected paper credentials and never on fork pull requests.

## Deterministic fixtures

- Immutable daily, hourly, minute, and quote fixtures with feed, timestamp, finality, and adjustment metadata.
- A fake exchange clock covering normal days, early closes, holidays, DST transitions, and unscheduled closures.
- Three-file TC2000 batches for accepted, empty, duplicate, malformed, mixed-date, stale, partial, and hash-mismatch cases.
- A scripted broker supporting acknowledgements, rejections, partial fills, delayed events, duplicate events, out-of-order events, 429, 5xx, timeouts, and disconnects.
- A database fault injector failing before commit, after intent commit, during event persistence, and during shutdown.
- Corporate-action fixtures for splits, symbol changes, dividends, delistings, and halts.

## Traceability matrix

| Requirement or risk | Required evidence |
|---|---|
| SMA10/20/50/200 and volume EMA22 | Golden-vector unit tests on daily and hourly series, warm-up/missing-bar cases |
| ADR20% and ATR20% | Hand-calculated vectors; previous-close denominator proof; gaps and zero/invalid prior close |
| Average dollar volume | Hand-calculated `mean(close * volume, 20)`; missing/zero volume |
| 20/60/120 strength | Point-in-time cutoff tests and universe percentile ties; no future rows |
| Trend slopes | Exact normalized formula, lookback, threshold-boundary and zero-denominator tests |
| Pivots/contraction | Golden patterns plus generated higher-low/lower-high and insufficient-bar cases |
| MA proximity/narrow candle/volume decline | Boundary tests and independently logged component results |
| Breakout crossing | Below-to-above edge, already-above stale candidate, exact touch, chase/gap cap, duplicate tick |
| Time-normalized breakout volume | No full-day morning comparison; same elapsed-session bucket; missing baseline rejection |
| TC2000 importer | Atomic three-file commit; stale/partial/empty/wrong-date/invalid/duplicate rejection; raw hash retention |
| Candidate modes | Exact 3-of-3, 2-of-3, and union sets; only strict set execution-eligible |
| Sizing | Whole-share floor; 1% ceiling/downward-only normal configuration; conservative fill; each cap; committed risk; zero-share and invalid-stop rejection; worse fill never increases quantity |
| Stop width | Zero, negative, too tight, too wide, and valid boundaries |
| Exposure | Per-position, portfolio, concurrency, buying power, open/pending risk, one symbol invariant |
| Paper endpoint | Every scheme/host/path variation except exact allowlist terminates before network; account verification failure blocks readiness |
| Entry orders | Marketable-limit/stop-limit price ceiling, TTL, cancel, chase, session close, partial entry fill |
| Stop protection | Stop acknowledgement, rejection, timeout, partial-fill quantity, missing-stop block, bounded recovery |
| 5R partial | R from actual VWAP and initial stop; rounding; positions under four shares; exactly once across duplicate events/restart |
| Breakeven stop | Only after partial fill; price equals actual VWAP; remaining quantity exact; replacement races |
| Daily-close exit | Completed official daily bar only; next-session scheduling; near-close shadow; overnight gap record |
| Gap-through stop | Fill/slippage model and planned-vs-realized R divergence |
| Broker failures | REST timeout, 429 with retry guidance, 5xx, stream disconnect, stale snapshot, out-of-order/duplicate events |
| Reconciliation | Missing/extra order, quantity/status/fill mismatch; broker actuals win; incident visible; entries blocked |
| Restart | Crash/restart during every order state and every gap between intent, acknowledgement, fill, stop, partial, replacement, and final exit |
| Persistence failure | No order before intent commit; uncertain post-ack state reconciles without duplicate submission |
| Calendar/clock | Holidays, early closes, DST, timezone conversion, clock drift, unscheduled closure |
| Corporate actions | Adjusted research/unadjusted execution separation; split quantity/price handling; symbol/halting blocks; dividend limitation |
| Security | Secret scan, dependency scan, log-redaction tests, authz tests, safe `.env.example`, signed-URL/header rejection |
| AI boundary | AI service receives no mutation protocol; output cannot change config, eligibility, state, risk, or order intent |
| Emergency entry block | New entries stop immediately while existing stop, partial, final-exit, and reconciliation management continues |

## State invariants

Property and model-based tests must hold these invariants for every generated event sequence:

1. No broker request is sent through a non-paper adapter.
2. No entry intent exists unless all freshness, batch, session, persistence, reconciliation, duplicate, buying-power, and risk guards passed.
3. At most one pending entry or open trade case exists per symbol.
4. Filled quantity is either covered by an acknowledged valid stop, in an actively managed final exit, or globally blocks new entries in `RISK_BLOCKED`.
5. Position and order quantities never become negative or exceed reconciled broker quantity.
6. A 5R action creates at most one logical sell intent across duplicate events and restarts.
7. A partial is never zero shares and never exceeds open quantity. Remaining quantity must stay protected.
8. A final SMA10 exit cannot be decided from an unfinished daily bar.
9. Broker/local discrepancy remains visible and blocks new risk.
10. Terminal cases reject stale delayed events except reconciliation evidence.

## Crash matrix

Restart tests inject a crash:

- Before and after entry-intent commit
- Before request, after timeout, after acknowledgement, and after partial entry fill
- Before stop request, after stop acknowledgement, and after stop rejection
- Before and after the one-time 5R action commit
- During partial fills and before/after breakeven replacement acknowledgement
- After daily-close signal, before next-open exit, during final fill, and during conflicting stop cancellation
- During REST snapshot, stream checkpoint, incident creation, and graceful shutdown

Each case must recover through broker reconciliation, reuse idempotency keys, preserve history, prevent duplicate positions, and keep readiness false while actual state or protection is uncertain.

## Backtest validity

- A datum is usable only after its event timestamp. Tests poison future rows and assert results do not change.
- Intraday entry stop references use only the running regular-session low through that event.
- Daily SMA10 exit signals appear only after official bar completion and fill no earlier than the next executable session.
- Universe membership and strength ranks use point-in-time constituents. Any survivorship limitation is explicit.
- Adjusted research bars and unadjusted order-reconstruction bars remain separate.
- Simulator tests cover spread, latency slippage, partial fills, stop-limit nonfills, overnight gaps, halts, delistings, corporate actions, commissions, and regulatory fees.
- Development, validation, and final out-of-sample datasets have immutable fingerprints. Walk-forward windows cannot overlap improperly.
- Parameter reports favor stability and sample adequacy, not maximum backtest return.

## CI versus paper sandbox

Pull-request CI uses fakes only and runs formatting, linting, type checking, unit, property, integration, state-machine, migration, secret, and dependency checks. GitHub Actions never runs the persistent bot.

The Alpaca paper sandbox suite is manually dispatched from a protected environment, verifies the exact paper endpoint first, uses bounded isolated test orders, records reconciliation/cleanup evidence, and does not run on fork contributions. Strategy-triggered orders are outside the sandbox suite.

## Readiness evidence

PAPER_AUTO requires the specification's operational evidence plus a machine-readable acceptance manifest. Engineering readiness is reported separately from backtest and forward-test performance statistics.
