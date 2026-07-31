# ADR-0002: Separate Candidate, Decision, and Broker Authority

- Status: Accepted for design
- Date: 2026-07-31

## Decision

TC2000 exports authorize candidate membership only. Independently configured market data authorizes indicator and signal evidence. Alpaca paper snapshots and events authorize actual account, order, fill, and position facts. Disagreement is preserved as provenance or a reconciliation incident and cannot be silently collapsed.

## Consequences

- Symbol-only TC2000 files cannot prove source rank or execution prices.
- Reports identify provider, feed, timestamp, adjustment status, and payload hash.
- Broker actuals win reconciliation while local discrepancies remain visible and block new risk.
