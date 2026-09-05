from datetime import date, datetime

from app.models.booking import BookingRecord, BookingType
from app.services.consistency_checker import (
    detect_schedule_conflicts,
    find_accommodation_gaps,
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


def test_detects_overlapping_events() -> None:
    train = _booking(
        BookingType.TRAIN,
        datetime(2026, 8, 17, 10, 32),
        datetime(2026, 8, 17, 13, 44),
    )
    tour = _booking(
        BookingType.ACTIVITY,
        datetime(2026, 8, 17, 13, 0),
        datetime(2026, 8, 17, 15, 0),
    )

    conflicts = detect_schedule_conflicts([train, tour])

    assert conflicts == [(train, tour)]


def test_no_conflict_for_back_to_back_events() -> None:
    first = _booking(
        BookingType.ACTIVITY,
        datetime(2026, 8, 17, 10, 0),
        datetime(2026, 8, 17, 12, 0),
    )
    second = _booking(
        BookingType.ACTIVITY,
        datetime(2026, 8, 17, 12, 0),
        datetime(2026, 8, 17, 14, 0),
    )

    assert detect_schedule_conflicts([first, second]) == []


def test_hotel_overlap_is_not_a_conflict() -> None:
    hotel = _booking(
        BookingType.HOTEL,
        datetime(2026, 8, 17, 14, 0),
        datetime(2026, 8, 19, 10, 0),
    )
    dinner = _booking(
        BookingType.ACTIVITY,
        datetime(2026, 8, 18, 19, 0),
        datetime(2026, 8, 18, 21, 0),
    )

    assert detect_schedule_conflicts([hotel, dinner]) == []


def test_finds_missing_accommodation_night() -> None:
    # Scenario 1: hotels cover Aug 15-19 and Aug 20-22, flight leaves Aug 22.
    # The night of Aug 19 has no accommodation.
    bookings = [
        _booking(
            BookingType.FLIGHT,
            datetime(2026, 8, 15, 10, 30),
            datetime(2026, 8, 15, 17, 55),
        ),
        _booking(
            BookingType.HOTEL,
            datetime(2026, 8, 15, 15, 0),
            datetime(2026, 8, 19, 10, 0),
        ),
        _booking(
            BookingType.HOTEL,
            datetime(2026, 8, 20, 15, 0),
            datetime(2026, 8, 22, 10, 0),
        ),
        _booking(
            BookingType.FLIGHT,
            datetime(2026, 8, 22, 15, 55),
            datetime(2026, 8, 23, 10, 25),
        ),
    ]

    assert find_accommodation_gaps(bookings) == [date(2026, 8, 19)]


def test_no_gaps_when_fully_covered() -> None:
    bookings = [
        _booking(
            BookingType.HOTEL,
            datetime(2026, 8, 15, 15, 0),
            datetime(2026, 8, 17, 10, 0),
        ),
        _booking(
            BookingType.HOTEL,
            datetime(2026, 8, 17, 14, 0),
            datetime(2026, 8, 18, 10, 0),
        ),
    ]

    assert find_accommodation_gaps(bookings) == []


def test_empty_bookings_returns_no_gaps() -> None:
    assert find_accommodation_gaps([]) == []
