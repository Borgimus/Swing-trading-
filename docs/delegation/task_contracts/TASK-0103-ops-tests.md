# TASK-0103: Health, Logging, Calendar, and Fake Tests

## Objective

Enumerate Phase 1 tests for health/readiness, structured redacted JSON logging, exchange-session boundaries, paper-only broker guards, and deterministic fakes.

## Permitted scope

- Inspect Phase 0 architecture, test plan, and implementation plan.
- Return analysis only. Do not modify files.

## Required output

1. Test matrix by component.
2. Readiness truth table.
3. Log-redaction cases.
4. Calendar cases for DST, holidays, and early closes.
5. Fake-adapter behavior needed by later phases without implementing orders.

## Acceptance criteria

- Any non-paper endpoint is rejected before transport invocation.
- Readiness is false until startup reconciliation and persistence checks pass.
- Logs never expose secret headers, tokens, credentials, or signed URLs.
- Fakes are deterministic and contain no external connections.

## Prohibited actions

- No file edits, secrets, broker access, commits, pushes, deployments, or self-approval.
- No order submission interface, strategy logic, risk changes, or live endpoint examples.

## Budget

Low reasoning effort. Target at most 1,400 output tokens.
