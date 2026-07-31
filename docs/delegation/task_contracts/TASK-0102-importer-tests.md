# TASK-0102: Atomic TC2000 Import Test Review

## Objective

Enumerate deterministic Phase 1 tests for an importer that accepts exactly three symbol-only files atomically, preserves raw bytes and SHA-256 hashes, validates filenames/date/symbols/freshness, and derives 3-of-3, 2-of-3, and union candidate sets.

## Permitted scope

- Inspect Phase 0 requirements, TC2000 setup, schema, and test plan.
- Return analysis only. Do not modify files.

## Required output

1. Test case table with inputs, expected result/error code, and persistence assertions.
2. Transaction/failure-injection cases.
3. Symbol-normalization edge cases without inventing unsupported instruments.
4. Property-test invariants.
5. Minimum acceptance set for Phase 1.

## Acceptance criteria

- Covers incomplete, empty, duplicate, malformed, stale, mixed-date, timestamp-skew, content mismatch, database failure, and replay cases.
- Proves rejected batches never activate candidates.
- Preserves rejected raw evidence when persistence remains available.
- Does not infer TC2000 source rank from symbol-only files.

## Prohibited actions

- No file edits, secrets, broker access, commits, pushes, deployments, or self-approval.
- No strategy threshold, risk, endpoint, or symbol-universe policy changes.

## Budget

Low reasoning effort. Target at most 1,500 output tokens.
