# Dependency Pinning and Upgrades

Python is constrained to 3.12 for Phase 1. Every direct runtime and development dependency is exactly pinned in `pyproject.toml`, and every transitive package is locked in `uv.lock`.

## Install

```bash
uv sync --frozen --all-groups
```

CI always uses the frozen lock. Runtime containers will install the runtime-only frozen set.

## Reviewed upgrade procedure

1. Create a dedicated branch for one dependency family.
2. Review upstream release notes, security advisories, Python support, and migration notes.
3. Change the explicit version in `pyproject.toml`.
4. Run `uv lock --upgrade-package PACKAGE`.
5. Run formatting, lint, typing, all tests, migration checks, secret scanning, and `pip-audit`.
6. Review the complete lockfile diff and transitive additions/removals.
7. Record database, calendar, API, or safety-boundary implications in the pull request.
8. Require normal review. Dependabot changes are never auto-merged.

No trading, broker-order, technical-analysis, AI, or market-data SDK is permitted without a separate architecture and security review.
