from __future__ import annotations

from urllib.parse import urlsplit

from swing_trading.broker.interface import PaperAccountIdentity, TransportFactory

ALPACA_PAPER_BASE_URL = "https://paper-api.alpaca.markets"


class PaperBoundaryViolation(RuntimeError):
    """Raised before transport creation when the paper-only boundary is violated."""


class PaperAccountVerificationError(RuntimeError):
    """Raised when the broker identity does not prove an active paper account."""


class AlpacaPaperBoundary:
    @staticmethod
    def validate_url(candidate: str) -> None:
        parsed = urlsplit(candidate)
        if (
            candidate != ALPACA_PAPER_BASE_URL
            or parsed.scheme != "https"
            or parsed.hostname != "paper-api.alpaca.markets"
            or parsed.port is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise PaperBoundaryViolation("Alpaca endpoint is not the exact paper endpoint")

    @classmethod
    def create_transport(cls, factory: TransportFactory) -> object:
        cls.validate_url(ALPACA_PAPER_BASE_URL)
        return factory(ALPACA_PAPER_BASE_URL)

    @staticmethod
    def verify_account(identity: PaperAccountIdentity) -> None:
        if not identity.is_paper or identity.status.upper() != "ACTIVE":
            raise PaperAccountVerificationError("broker identity is not an active paper account")
