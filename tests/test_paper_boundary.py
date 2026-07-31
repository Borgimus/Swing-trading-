from __future__ import annotations

from datetime import UTC, datetime

import pytest

from swing_trading.broker.alpaca_paper import (
    ALPACA_PAPER_BASE_URL,
    AlpacaPaperBoundary,
    PaperAccountVerificationError,
    PaperBoundaryViolation,
)
from swing_trading.broker.interface import PaperAccountIdentity
from swing_trading.testing.fakes import RecordingTransportFactory


@pytest.mark.parametrize(
    "candidate",
    [
        "http://paper-api.alpaca.markets",
        "https://api.alpaca.markets",
        "https://paper-api.alpaca.markets.evil.example",
        "https://paper-api.alpaca.markets:443",
        "https://paper-api.alpaca.markets/",
        "https://paper-api.alpaca.markets/v2",
        "https://user:password@paper-api.alpaca.markets",  # pragma: allowlist secret
        "https://paper-api.alpaca.markets?redirect=1",
        "https://paper-api.alpaca.markets#fragment",
        "paper-api.alpaca.markets",
        "",
    ],
)
def test_every_endpoint_variation_is_rejected(candidate: str) -> None:
    with pytest.raises(PaperBoundaryViolation):
        AlpacaPaperBoundary.validate_url(candidate)


def test_transport_is_created_only_with_compiled_paper_endpoint() -> None:
    factory = RecordingTransportFactory()

    AlpacaPaperBoundary.create_transport(factory)

    assert factory.calls == [ALPACA_PAPER_BASE_URL]


def test_rejected_endpoint_never_invokes_transport() -> None:
    factory = RecordingTransportFactory()

    with pytest.raises(PaperBoundaryViolation):
        AlpacaPaperBoundary.validate_url("https://api.alpaca.markets")

    assert factory.calls == []


def test_account_identity_must_prove_active_paper_account() -> None:
    observed_at = datetime.now(UTC)
    AlpacaPaperBoundary.verify_account(
        PaperAccountIdentity("safe-fingerprint", True, "ACTIVE", observed_at)
    )

    with pytest.raises(PaperAccountVerificationError):
        AlpacaPaperBoundary.verify_account(
            PaperAccountIdentity("safe-fingerprint", False, "ACTIVE", observed_at)
        )
