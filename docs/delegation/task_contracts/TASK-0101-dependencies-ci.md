# TASK-0101: Phase 1 Dependency and CI Review

## Objective

Recommend the smallest Python 3.12 dependency and CI toolchain that can support Phase 1: Pydantic configuration, PostgreSQL plus SQLite tests, migrations, an ASGI health API, exchange calendars, JSON logging, tests, linting, typing, secret scanning, and dependency scanning.

## Permitted scope

- Inspect Phase 0 documents and current repository inventory.
- Return analysis only. Do not modify files.

## Required output

1. Runtime and development dependency table with purpose and risk.
2. Pinning and upgrade workflow.
3. GitHub Actions job outline with fork-safe credential behavior.
4. Risks from heavy/transitive packages or platform-specific wheels.
5. Minimal validation commands.

## Acceptance criteria

- Python 3.12 or newer.
- PostgreSQL deployment and SQLite test support.
- GitHub Actions is CI only and never receives broker credentials.
- Dependency and secret scanning are included.
- Recommends no trading, AI, or broker-order SDK.

## Prohibited actions

- No file edits, secrets, broker access, commits, pushes, deployments, or self-approval.
- No changes to strategy, risk, endpoint, or phase-gate rules.

## Budget

Low reasoning effort. Target at most 1,400 output tokens.
