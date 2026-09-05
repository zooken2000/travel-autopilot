from datetime import datetime

from app.models.alert import AlertType
from app.models.booking import BookingRecord, BookingType
from app.models.trip_state import TripState
from app.services.decision_engine import (
    check_departure,
    check_free_time,
    evaluate_trip,
)


def _booking(
    booking_type: BookingType,
    start: datetime,
    end: datetime,
    provider: str = "Test Provider",
) -> BookingRecord:
    return BookingRecord(
        booking_type=booking_type,
        provider_name=provider,
        start_time=start,
        end_time=end,
        start_location="A",
        end_location="B",
    )


def _state(
    current_time: datetime,
    bookings: list[BookingRecord],
    location: str | None = None,
) -> TripState:
    return TripState(
        trip_id="test",
        current_time=current_time,
        current_location=location,
        bookings=bookings,
        updated_at=current_time,
    )


def _covered_stay(start: datetime, end: datetime) -> BookingRecord:
    return _booking(BookingType.HOTEL, start, end, "Hotel")


def test_scenario3_airport_departure_alert_fires() -> None:
    # Flight 15:55, recommended arrival 12:55, now 12:30 -> alert.
    flight = _booking(
        BookingType.FLIGHT,
        datetime(2026, 8, 22, 15, 55),
        datetime(2026, 8, 23, 10, 25),
        "Swiss LX160",
    )
    hotel = _covered_stay(
        datetime(2026, 8, 21, 15, 0), datetime(2026, 8, 22, 10, 0)
    )
    state = _state(datetime(2026, 8, 22, 12, 30), [hotel, flight])

    alert = check_departure(state)

    assert alert is not None
    assert alert.alert_type == AlertType.DEPARTURE_REQUIRED
    assert "time to leave" in alert.message.lower()


def test_departure_alert_silent_when_plenty_of_time() -> None:
    flight = _booking(
        BookingType.FLIGHT,
        datetime(2026, 8, 22, 15, 55),
        datetime(2026, 8, 23, 10, 25),
    )
    state = _state(datetime(2026, 8, 22, 8, 0), [flight])

    assert check_departure(state) is None


def test_scenario2_free_time_alert() -> None:
    # 14:00 now, dinner at 19:00, in Zermatt -> 5h free time.
    dinner = _booking(
        BookingType.ACTIVITY,
        datetime(2026, 8, 18, 19, 0),
        datetime(2026, 8, 18, 21, 0),
        "Whymper-Stube",
    )
    state = _state(datetime(2026, 8, 18, 14, 0), [dinner], location="Zermatt")

    alert = check_free_time(state)

    assert alert is not None
    assert alert.alert_type == AlertType.FREE_TIME
    assert "Zermatt" in alert.message
    assert alert.requires_user_action is False


def test_scenario1_missing_accommodation_via_evaluate_trip() -> None:
    bookings = [
        _covered_stay(datetime(2026, 8, 15, 15, 0), datetime(2026, 8, 19, 10, 0)),
        _covered_stay(datetime(2026, 8, 20, 15, 0), datetime(2026, 8, 22, 10, 0)),
    ]
    state = _state(datetime(2026, 8, 16, 9, 0), bookings)

    alerts = evaluate_trip(state)

    conflict_alerts = [
        a for a in alerts if a.alert_type == AlertType.BOOKING_CONFLICT
    ]
    assert len(conflict_alerts) == 1
    assert "August 19" in conflict_alerts[0].message


def test_evaluate_trip_is_silent_when_all_is_well() -> None:
    # Fully covered nights, next event far away but below free-time threshold.
    bookings = [
        _covered_stay(datetime(2026, 8, 15, 15, 0), datetime(2026, 8, 17, 10, 0)),
        _booking(
            BookingType.ACTIVITY,
            datetime(2026, 8, 16, 12, 0),
            datetime(2026, 8, 16, 14, 0),
        ),
    ]
    state = _state(datetime(2026, 8, 16, 10, 0), bookings)

    assert evaluate_trip(state) == []


def test_departure_alert_suppresses_free_time() -> None:
    # 3h25m until the flight: departure alert fires, free-time stays silent.
    flight = _booking(
        BookingType.FLIGHT,
        datetime(2026, 8, 22, 15, 55),
        datetime(2026, 8, 23, 10, 25),
    )
    hotel = _covered_stay(
        datetime(2026, 8, 21, 15, 0), datetime(2026, 8, 22, 10, 0)
    )
    state = _state(datetime(2026, 8, 22, 12, 30), [hotel, flight])

    alerts = evaluate_trip(state)

    types = [a.alert_type for a in alerts]
    assert AlertType.DEPARTURE_REQUIRED in types
    assert AlertType.FREE_TIME not in types


def test_past_accommodation_gap_is_not_reported() -> None:
    # Gap night Aug 19 is in the past on Aug 22: nothing to act on.
    from app.services.decision_engine import check_accommodation

    bookings = [
        _covered_stay(datetime(2026, 8, 15, 15, 0), datetime(2026, 8, 19, 10, 0)),
        _covered_stay(datetime(2026, 8, 20, 15, 0), datetime(2026, 8, 22, 10, 0)),
        _booking(
            BookingType.FLIGHT,
            datetime(2026, 8, 22, 15, 55),
            datetime(2026, 8, 23, 10, 25),
        ),
    ]
    state = _state(datetime(2026, 8, 22, 12, 30), bookings)

    assert check_accommodation(state) is None
