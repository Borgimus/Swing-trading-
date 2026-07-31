from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PaperAccountIdentity:
    account_id_fingerprint: str
    is_paper: bool
    status: str
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class BrokerPositionSnapshot:
    symbol: str
    quantity: int
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class BrokerOrderSnapshot:
    broker_order_id: str
    client_order_id: str
    symbol: str
    status: str
    observed_at: datetime


class PaperBrokerReader(Protocol):
    """Phase 1 exposes broker reads only. There is deliberately no order mutation method."""

    def account_identity(self) -> PaperAccountIdentity: ...

    def positions(self) -> tuple[BrokerPositionSnapshot, ...]: ...

    def open_orders(self) -> tuple[BrokerOrderSnapshot, ...]: ...


class TransportFactory(Protocol):
    def __call__(self, base_url: str) -> object: ...
