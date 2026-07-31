# TASK-0003: Test Strategy and Delivery Gates

## Objective

Design a risk-focused test matrix and phased implementation plan for the supplied paper-only trading system.

## Permitted scope

- Inspect the user-supplied build specification in the current conversation.
- Do not modify repository files.
- Return analysis only.

## Relevant context and interfaces

- Tests must cover mathematical rules, imports, state transitions, broker failures, restart recovery, reconciliation, market calendars, security, and backtest bias.
- Delivery must progress through BACKTEST, SHADOW, PAPER_CONFIRM, and then PAPER_AUTO after explicit gates.
- GitHub Actions is CI only, never the persistent trading runtime.

## Required output

A Markdown response with:

1. Test pyramid and fixtures/fakes
2. Traceability matrix from risk area to test level and evidence
3. Property/state-machine invariants
4. Failure-injection and restart matrix
5. Backtest validity checks
6. CI and opt-in paper-sandbox separation
7. Phased delivery plan with entry and exit gates

## Acceptance criteria

- Covers every minimum test named in the specification.
- Defines evidence for paper-endpoint rejection, no duplicate orders, no unprotected positions, and exactly-once 5R behavior.
- Includes DST, holidays, early closes, clock drift, stale data, DB failures, 429/5xx/timeouts, streaming disconnects, and partial fills.
- Separates engineering readiness from statistical strategy evaluation.

## Validation

Supervisor will map the proposal back to all required test and PAPER_AUTO acceptance criteria.

## Prohibited actions

- No file changes, commits, pushes, deployments, network calls, broker connections, credential access, or self-approval.
- No changes to thresholds, strategy rules, risk limits, or runtime configuration.

## Budget

Low reasoning effort. Target at most 2,000 output tokens.
