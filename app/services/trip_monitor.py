"""Deterministic monitoring utilities.

These functions contain NO LLM calls. The agent uses them as tools;
tests exercise them directly.
"""

from datetime import timedelta

from app.models.booking import BookingRecord
from app.models.trip_state import TripState


def find_next_event(trip_state: TripState) -> BookingRecord | None:
    """Return the next booking that starts after the current time, or None."""
    upcoming = [
        booking
        for booking in trip_state.bookings
        if booking.start_time > trip_state.current_time
    ]
    if not upcoming:
        return None
    return min(upcoming, key=lambda booking: booking.start_time)


def calculate_time_until_event(
    trip_state: TripState,
    event: BookingRecord,
) -> timedelta:
    """Time remaining from the trip's current time until the event starts.

    Negative if the event has already started.
    """
    return event.start_time - trip_state.current_time


def detect_free_time(
    trip_state: TripState,
    threshold: timedelta = timedelta(hours=3),
) -> timedelta | None:
    """Return the free-time gap until the next event if it exceeds threshold.

    Returns None when there is no upcoming event, the gap is below the
    threshold, or the next event is on another day (an overnight gap is
    normal, not "free time" worth interrupting the user about).
    """
    next_event = find_next_event(trip_state)
    if next_event is None:
        return None
    if next_event.start_time.date() != trip_state.current_time.date():
        return None
    gap = calculate_time_until_event(trip_state, next_event)
    if gap >= threshold:
        return gap
    return None
