from __future__ import annotations

from fastapi import FastAPI, Response, status

from swing_trading import __version__
from swing_trading.health.readiness import ReadinessRegistry


def create_app(readiness: ReadinessRegistry | None = None) -> FastAPI:
    registry = readiness or ReadinessRegistry()
    app = FastAPI(title="TC2000 Alpaca Swing", version=__version__)

    @app.get("/health/live")
    def liveness() -> dict[str, str]:
        return {"status": "alive", "version": __version__}

    @app.get("/health/ready")
    def ready(response: Response) -> dict[str, object]:
        snapshot = registry.snapshot()
        if not snapshot.ready:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "ready": snapshot.ready,
            "checks": snapshot.checks,
            "blockers": snapshot.blockers,
            "observed_at": snapshot.observed_at.isoformat(),
        }

    app.state.readiness = registry
    return app


app = create_app()
