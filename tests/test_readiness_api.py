from __future__ import annotations

from fastapi.testclient import TestClient

from swing_trading.api.app import create_app
from swing_trading.health.readiness import REQUIRED_READINESS_CHECKS, ReadinessRegistry


def test_liveness_is_independent_of_readiness() -> None:
    client = TestClient(create_app())

    assert client.get("/health/live").status_code == 200
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["ready"] is False


def test_every_required_predicate_must_pass() -> None:
    readiness = ReadinessRegistry()
    client = TestClient(create_app(readiness))

    for name in REQUIRED_READINESS_CHECKS:
        readiness.set_check(name, True)
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["ready"] is True

    readiness.set_check("positions_protected", False)
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["blockers"] == ["positions_protected"]


def test_restart_resets_all_readiness_evidence() -> None:
    readiness = ReadinessRegistry()
    for name in REQUIRED_READINESS_CHECKS:
        readiness.set_check(name, True)

    readiness.reset_for_restart()

    snapshot = readiness.snapshot()
    assert snapshot.ready is False
    assert snapshot.blockers == REQUIRED_READINESS_CHECKS
