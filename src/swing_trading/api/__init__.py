"""Authenticated application API boundary. Phase 1 exposes health only."""

from swing_trading.api.app import create_app

__all__ = ["create_app"]
