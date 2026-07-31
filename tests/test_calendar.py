from __future__ import annotations

from datetime import UTC, date, datetime

from swing_trading.calendars.exchange import NyseCalendar


def test_dst_changes_utc_open_without_changing_local_session() -> None:
    calendar = NyseCalendar()
    winter = calendar.session_bounds(date(2026, 1, 2))
    summer = calendar.session_bounds(date(2026, 7, 31))

    assert winter is not None and winter.opens_at.hour == 14 and winter.opens_at.minute == 30
    assert summer is not None and summer.opens_at.hour == 13 and summer.opens_at.minute == 30


def test_holiday_and_injected_unscheduled_closure_are_closed() -> None:
    closure = date(2026, 7, 31)
    calendar = NyseCalendar(unscheduled_closures=frozenset({closure}))

    assert calendar.is_session(date(2026, 12, 25)) is False
    assert calendar.is_session(closure) is False


def test_day_after_thanksgiving_is_early_close() -> None:
    bounds = NyseCalendar().session_bounds(date(2026, 11, 27))

    assert bounds is not None
    assert bounds.early_close is True
    assert (bounds.closes_at - bounds.opens_at).total_seconds() == 3.5 * 60 * 60


def test_close_is_exclusive_for_entry_session() -> None:
    calendar = NyseCalendar()
    bounds = calendar.session_bounds(date(2026, 7, 31))
    assert bounds is not None

    assert calendar.is_regular_session_time(bounds.opens_at) is True
    assert calendar.is_regular_session_time(bounds.closes_at) is False
    assert calendar.is_regular_session_time(datetime(2026, 7, 31, 12, 0, tzinfo=UTC)) is False
