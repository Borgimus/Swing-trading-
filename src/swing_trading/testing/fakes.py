from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from swing_trading.broker.interface import (
    BrokerOrderSnapshot,
    BrokerPositionSnapshot,
    PaperAccountIdentity,
)


@dataclass(slots=True)
class FakeClock:
    current: datetime

    def now(self) -> datetime:
        if self.current.tzinfo is None:
            raise ValueError("fake clock must be timezone-aware")
        return self.current

    def advance(self, delta: timedelta) -> None:
        self.current += delta


@dataclass(slots=True)
class FakeCalendar:
    sessions: set[date]

    def is_session(self, market_date: date) -> bool:
        return market_date in self.sessions


@dataclass(slots=True)
class RecordingTransportFactory:
    calls: list[str] = field(default_factory=list)

    def __call__(self, base_url: str) -> object:
        self.calls.append(base_url)
        return object()


@dataclass(slots=True)
class FakePaperBroker:
    identity: PaperAccountIdentity
    position_values: tuple[BrokerPositionSnapshot, ...] = ()
    order_values: tuple[BrokerOrderSnapshot, ...] = ()
    calls: list[str] = field(default_factory=list)

    def account_identity(self) -> PaperAccountIdentity:
        self.calls.append("account_identity")
        return self.identity

    def positions(self) -> tuple[BrokerPositionSnapshot, ...]:
        self.calls.append("positions")
        return self.position_values

    def open_orders(self) -> tuple[BrokerOrderSnapshot, ...]:
        self.calls.append("open_orders")
        return self.order_values
