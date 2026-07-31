# TC2000 Alpaca Swing

Production-oriented research and automation for a long-only US-stock swing strategy sourced from an unverified social-media description.

## Safety boundary

- Alpaca paper trading only.
- No live-trading mode, endpoint, feature flag, or deployment phase.
- TC2000 candidates enter through operator-exported symbol files. The project does not claim or invent a TC2000 API.
- Deterministic rules own every qualification, risk, order, reconciliation, and exit decision.
- AI output is advisory and cannot reach the broker mutation interface.
- Paper results are simulated evidence. They do not establish profitability or live-execution performance.

## Current phase

Phase 0 contains the reviewed requirements audit and system design. It intentionally contains no trading implementation. See [the phased plan](docs/implementation_plan.md).

Proposed repository name: `tc2000-alpaca-swing`.

## Design index

- [Requirements audit](docs/requirements_audit.md)
- [Architecture](docs/architecture.md)
- [State machine](docs/state_machine.md)
- [TC2000 setup and handoff](docs/tc2000_setup.md)
- [Database schema](docs/database_schema.md)
- [Test plan](docs/test_plan.md)
- [Implementation plan](docs/implementation_plan.md)
- [Delegation log](docs/delegation_log.md)

## License

MIT. The license includes the standard warranty disclaimer. This repository does not provide investment advice.
