from datetime import datetime

import pytest

from app.models.booking import BookingRecord, BookingType
from app.models.trip_state import TripState
from app.services.itinerary_generator import (
    ItineraryBlockedError,
    build_plan_prompt,
    generate_day_plan,
)


def _booking(booking_type, start, end, provider="Test"):
    return BookingRecord(
        booking_type=booking_type,
        provider_name=provider,
        start_time=start,
        end_time=end,
        start_location="Zermatt",
        end_location="Zermatt",
    )


def _state(bookings, current_time=datetime(2026, 8, 18, 9, 0)):
    return TripState(
        trip_id="t",
        current_time=current_time,
        current_location="Zermatt",
        bookings=bookings,
        updated_at=current_time,
    )


def test_generation_blocked_by_accommodation_gap() -> None:
    bookings = [
        _booking(BookingType.HOTEL, datetime(2026, 8, 17, 14, 0), datetime(2026, 8, 19, 10, 0)),
        _booking(BookingType.HOTEL, datetime(2026, 8, 20, 15, 0), datetime(2026, 8, 21, 10, 0)),
    ]
    with pytest.raises(ItineraryBlockedError) as exc:
        generate_day_plan(_state(bookings), invoke=lambda p: "should not be called")
    assert "August 19" in str(exc.value)


def test_generation_succeeds_when_consistent() -> None:
    bookings = [
        _booking(BookingType.HOTEL, datetime(2026, 8, 17, 14, 0), datetime(2026, 8, 19, 10, 0)),
        _booking(
            BookingType.ACTIVITY,
            datetime(2026, 8, 18, 19, 0),
            datetime(2026, 8, 18, 21, 0),
            "Whymper-Stube",
        ),
    ]
    plan = generate_day_plan(_state(bookings), invoke=lambda p: "09:30  Breakfast\n")
    assert plan == "09:30  Breakfast"


def test_prompt_lists_only_todays_events() -> None:
    bookings = [
        _booking(BookingType.HOTEL, datetime(2026, 8, 17, 14, 0), datetime(2026, 8, 19, 10, 0)),
        _booking(
            BookingType.ACTIVITY,
            datetime(2026, 8, 18, 19, 0),
            datetime(2026, 8, 18, 21, 0),
            "Whymper-Stube",
        ),
        _booking(
            BookingType.TRAIN,
            datetime(2026, 8, 20, 10, 0),
            datetime(2026, 8, 20, 13, 0),
            "SBB Later",
        ),
    ]
    prompt = build_plan_prompt(_state(bookings))
    assert "Whymper-Stube" in prompt
    assert "SBB Later" not in prompt
