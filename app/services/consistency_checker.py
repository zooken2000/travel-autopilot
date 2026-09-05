"""Deterministic consistency checks over bookings.

No LLM calls here: overlap detection and accommodation-gap detection are
pure datetime logic.
"""

from datetime import date, timedelta

from app.models.booking import BookingRecord, BookingType


def detect_schedule_conflicts(
    bookings: list[BookingRecord],
) -> list[tuple[BookingRecord, BookingRecord]]:
    """Return pairs of time-overlapping bookings that require presence.

    Hotels are excluded: staying at a hotel legitimately overlaps with
    dinners, trains, and other events.
    """
    timed = [
        booking
        for booking in bookings
        if booking.booking_type != BookingType.HOTEL
    ]
    timed.sort(key=lambda booking: booking.start_time)

    conflicts: list[tuple[BookingRecord, BookingRecord]] = []
    for i, first in enumerate(timed):
        for second in timed[i + 1 :]:
            if second.start_time >= first.end_time:
                break
            conflicts.append((first, second))
    return conflicts


def find_accommodation_gaps(bookings: list[BookingRecord]) -> list[date]:
    """Return the nights (check-in dates) with no hotel booking.

    A "night" is every date from the first booking's start date up to,
    but not including, the last booking's end date. A night is covered
    when a hotel booking spans it, or when the traveler is on overnight
    transport (a flight or train crossing that night).
    """
    if not bookings:
        return []

    trip_start = min(booking.start_time for booking in bookings).date()
    trip_end = max(booking.end_time for booking in bookings).date()

    covering_types = {BookingType.HOTEL, BookingType.FLIGHT, BookingType.TRAIN}
    covering = [
        booking
        for booking in bookings
        if booking.booking_type in covering_types
        and booking.start_time.date() < booking.end_time.date()
    ]

    gaps: list[date] = []
    night = trip_start
    while night < trip_end:
        covered = any(
            booking.start_time.date() <= night < booking.end_time.date()
            for booking in covering
        )
        if not covered:
            gaps.append(night)
        night += timedelta(days=1)
    return gaps
