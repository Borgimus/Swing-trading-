# ADR-0001: Hard Paper-Only Broker Boundary

- Status: Accepted for design
- Date: 2026-07-31

## Decision

The broker adapter has one compiled trading host allowlist entry: `https://paper-api.alpaca.markets`. Runtime configuration cannot supply a host or select live mode. Startup and every order mutation require successful paper-account verification. A mismatch terminates safely before any request to an unapproved host.

## Consequences

- A code change, review, and new release would be required to alter the boundary.
- Live credentials and live endpoints have no supported storage or execution path.
- Fake adapters cover CI. Protected opt-in integration tests use Alpaca paper only.
