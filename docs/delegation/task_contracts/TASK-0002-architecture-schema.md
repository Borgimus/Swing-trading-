# TASK-0002: Architecture, State Machine, and Schema Review

## Objective

Propose a paper-only system architecture, guarded state-machine model, and relational data model that satisfy the supplied build specification.

## Permitted scope

- Inspect the user-supplied build specification in the current conversation.
- Do not modify repository files.
- Return analysis only.

## Relevant context and interfaces

- Python 3.12+, PostgreSQL deployment, SQLite isolated tests only.
- Persistent Linux runtime, optional Windows export-folder companion with no broker authority.
- Alpaca paper REST snapshots plus trade-update stream.
- Atomic three-file TC2000 import batch.
- Deterministic event/state transitions with guards and idempotency keys.

## Required output

A Markdown response with:

1. Component boundaries and allowed dependencies
2. End-to-end event flow
3. State transition table including failure and restart paths
4. Relational schema grouped by concern, with primary keys and critical uniqueness constraints
5. Consistency and transaction boundaries
6. Paper-only security controls
7. Major design risks

## Acceptance criteria

- Broker state is authoritative for actual orders and positions, while discrepancies remain visible and block new risk.
- Missing-stop recovery is bounded and fail-closed.
- 5R partial execution is exactly once across retries and restarts.
- Daily-close exit waits for a completed official daily bar.
- No service outside deterministic execution can submit or mutate orders.
- Schema preserves raw imports, market-data provenance, decisions, transitions, orders, fills, incidents, and AI audit metadata.

## Validation

Supervisor will trace required trading lifecycles, restart scenarios, and duplicate-event handling through the proposal.

## Prohibited actions

- No file changes, commits, pushes, deployments, network calls, broker connections, or credential access.
- No strategy/risk/configuration changes and no self-approval.
- No implementation code.

## Budget

Low reasoning effort. Target at most 2,200 output tokens.
