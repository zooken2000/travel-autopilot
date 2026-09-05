from datetime import datetime, timedelta

from app.models.booking import BookingRecord, BookingType
from app.models.trip_state import TripState
from app.services.trip_monitor import (
    calculate_time_until_event,
    detect_free_time,
    find_next_event,
)


def _booking(
    start: datetime,
    end: datetime,
    booking_type: BookingType = BookingType.ACTIVITY,
) -> BookingRecord:
    return BookingRecord(
        booking_type=booking_type,
        provider_name="Test Provider",
        start_time=start,
        end_time=end,
        start_location="A",
        end_location="B",
    )


def _state(current_time: datetime, bookings: list[BookingRecord]) -> TripState:
    return TripState(
        trip_id="test",
        current_time=current_time,
        bookings=bookings,
        updated_at=current_time,
    )


def test_find_next_event_returns_earliest_upcoming() -> None:
    now = datetime(2026, 8, 18, 14, 0)
    past = _booking(datetime(2026, 8, 18, 9, 0), datetime(2026, 8, 18, 10, 0))
    dinner = _booking(datetime(2026, 8, 18, 19, 0), datetime(2026, 8, 18, 21, 0))
    later = _booking(datetime(2026, 8, 19, 10, 0), datetime(2026, 8, 19, 12, 0))

    result = find_next_event(_state(now, [later, past, dinner]))

    assert result is dinner


def test_find_next_event_returns_none_when_nothing_upcoming() -> None:
    now = datetime(2026, 8, 25, 0, 0)
    past = _booking(datetime(2026, 8, 18, 9, 0), datetime(2026, 8, 18, 10, 0))

    assert find_next_event(_state(now, [past])) is None


def test_calculate_time_until_event() -> None:
    now = datetime(2026, 8, 18, 14, 0)
    dinner = _booking(datetime(2026, 8, 18, 19, 0), datetime(2026, 8, 18, 21, 0))

    assert calculate_time_until_event(_state(now, [dinner]), dinner) == timedelta(
        hours=5
    )


def test_detect_free_time_above_threshold() -> None:
    # Scenario 2: 14:00 now, next event 19:00 -> 5h free time
    now = datetime(2026, 8, 18, 14, 0)
    dinner = _booking(datetime(2026, 8, 18, 19, 0), datetime(2026, 8, 18, 21, 0))

    assert detect_free_time(_state(now, [dinner])) == timedelta(hours=5)


def test_detect_free_time_below_threshold_is_silent() -> None:
    now = datetime(2026, 8, 18, 18, 0)
    dinner = _booking(datetime(2026, 8, 18, 19, 0), datetime(2026, 8, 18, 21, 0))

    assert detect_free_time(_state(now, [dinner])) is None


def test_detect_free_time_ignores_overnight_gap() -> None:
    # Next event is tomorrow: a long overnight gap is not "free time".
    now = datetime(2026, 8, 16, 9, 0)
    train = _booking(datetime(2026, 8, 17, 10, 32), datetime(2026, 8, 17, 13, 44))

    assert detect_free_time(_state(now, [train])) is None
