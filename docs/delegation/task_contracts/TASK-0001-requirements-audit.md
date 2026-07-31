# TASK-0001: Requirements Audit

## Objective

Classify the supplied build specification into immutable requirements, provisional strategy interpretations, and unresolved operator choices. Identify contradictions, unsafe ambiguity, and missing acceptance evidence.

## Permitted scope

- Inspect the user-supplied build specification in the current conversation.
- Do not modify repository files.
- Return analysis only.

## Relevant context and interfaces

- Version 1 is US-listed common-stock trading, long only, and Alpaca paper only.
- TC2000 supplies operator-exported candidate lists. No TC2000 API or UI automation may be invented.
- Deterministic controls are authoritative. AI cannot affect orders or risk decisions.
- Exact undefined thresholds must remain versioned hypotheses.

## Required output

A Markdown response with:

1. `Transcript or source facts`
2. `Project-mandated requirements`
3. `Provisional interpretations`
4. `Unresolved choices`
5. `Contradictions and safety concerns`
6. `Recommended Phase 0 decisions`

For each unresolved choice, state whether it blocks scaffolding, backtesting, shadow operation, PAPER_CONFIRM, or PAPER_AUTO.

## Acceptance criteria

- Does not promote any provisional threshold to a source fact.
- Identifies the official daily-close timing constraint and intraday breakout-day low lookahead hazard.
- Identifies paper-endpoint enforcement and missing-stop handling as non-negotiable controls.
- Separates engineering acceptance from profitability evidence.
- Contains no invented TC2000 or Alpaca capability.

## Validation

Supervisor will compare every item against the supplied specification and resolve inconsistencies during integration.

## Prohibited actions

- No file changes, commits, pushes, deployments, network calls, broker connections, or credential access.
- No changes to strategy rules, thresholds, risk limits, endpoint rules, or deployment settings.
- No self-approval or scope expansion.

## Budget

Low reasoning effort. Target at most 1,800 output tokens.
