from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock

REQUIRED_READINESS_CHECKS = (
    "configuration_valid",
    "database_persistent",
    "paper_endpoint_verified",
    "paper_account_verified",
    "broker_snapshot_fresh",
    "startup_reconciled",
    "positions_protected",
)


@dataclass(frozen=True, slots=True)
class ReadinessSnapshot:
    ready: bool
    checks: dict[str, bool]
    blockers: tuple[str, ...]
    observed_at: datetime


class ReadinessRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._checks = {name: False for name in REQUIRED_READINESS_CHECKS}

    def set_check(self, name: str, value: bool) -> None:
        if name not in self._checks:
            raise KeyError(f"unknown readiness check: {name}")
        with self._lock:
            self._checks[name] = value

    def reset_for_restart(self) -> None:
        with self._lock:
            for name in self._checks:
                self._checks[name] = False

    def snapshot(self) -> ReadinessSnapshot:
        with self._lock:
            checks = dict(self._checks)
        blockers = tuple(name for name, passed in checks.items() if not passed)
        return ReadinessSnapshot(
            ready=not blockers,
            checks=checks,
            blockers=blockers,
            observed_at=datetime.now(UTC),
        )
