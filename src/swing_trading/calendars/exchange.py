from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

import exchange_calendars
import pandas as pd


@dataclass(frozen=True, slots=True)
class SessionBounds:
    market_date: date
    opens_at: datetime
    closes_at: datetime
    early_close: bool


class NyseCalendar:
    def __init__(self, *, unscheduled_closures: frozenset[date] = frozenset()) -> None:
        self._calendar = exchange_calendars.get_calendar("XNYS")
        self._unscheduled_closures = unscheduled_closures

    def is_session(self, market_date: date) -> bool:
        if market_date in self._unscheduled_closures:
            return False
        return bool(self._calendar.is_session(pd.Timestamp(market_date)))

    def session_bounds(self, market_date: date) -> SessionBounds | None:
        if not self.is_session(market_date):
            return None
        label = pd.Timestamp(market_date)
        opens_at = self._calendar.session_open(label).to_pydatetime().astimezone(UTC)
        closes_at = self._calendar.session_close(label).to_pydatetime().astimezone(UTC)
        regular_duration_seconds = 6.5 * 60 * 60
        early_close = (closes_at - opens_at).total_seconds() < regular_duration_seconds
        return SessionBounds(market_date, opens_at, closes_at, early_close)

    def is_regular_session_time(self, instant: datetime) -> bool:
        if instant.tzinfo is None:
            raise ValueError("instant must be timezone-aware")
        utc_instant = instant.astimezone(UTC)
        market_date = utc_instant.astimezone(self._calendar.tz).date()
        bounds = self.session_bounds(market_date)
        return bool(bounds and bounds.opens_at <= utc_instant < bounds.closes_at)
