"""Deterministic decision engine.

Turns facts computed by trip_monitor / consistency_checker into Alerts
using fixed thresholds. No LLM calls: the agent consumes these results
and decides how to phrase/act on them, but WHETHER a threshold is
crossed is pure Python.

Silence is the default: evaluate_trip() returns an empty list when
nothing needs the traveler's attention.
"""

from datetime import timedelta

from app.models.alert import Alert, AlertType
from app.models.booking import BookingRecord, BookingType
from app.models.trip_state import TripState
from app.services.consistency_checker import (
    detect_schedule_conflicts,
    find_accommodation_gaps,
)
from app.services.trip_monitor import (
    calculate_time_until_event,
    detect_free_time,
    find_next_event,
)

# How long before a departure the traveler should be alerted.
# Flights: recommended airport arrival is 3h before departure, plus a
# 30-minute buffer to get to the airport.
DEPARTURE_LEAD: dict[BookingType, timedelta] = {
    BookingType.FLIGHT: timedelta(hours=3, minutes=30),
    BookingType.TRAIN: timedelta(minutes=30),
}

# Gaps shorter than this are not worth interrupting the traveler for.
FREE_TIME_THRESHOLD = timedelta(hours=3)


def check_accommodation(trip_state: TripState) -> Alert | None:
    """Scenario 1: upcoming nights with no accommodation booked.

    Past nights are not reported: they can no longer be acted on.
    """
    today = trip_state.current_time.date()
    gaps = [
        night
        for night in find_accommodation_gaps(trip_state.bookings)
        if night >= today
    ]
    if not gaps:
        return None
    nights = ", ".join(night.strftime("%B %-d") for night in gaps)
    return Alert(
        alert_type=AlertType.BOOKING_CONFLICT,
        title="Missing accommodation",
        message=f"⚠️ No accommodation found for {nights}.",
        requires_user_action=True,
    )


def check_conflicts(trip_state: TripState) -> Alert | None:
    """Overlapping bookings that both require the traveler's presence."""
    conflicts = detect_schedule_conflicts(trip_state.bookings)
    if not conflicts:
        return None
    first, second = conflicts[0]
    return Alert(
        alert_type=AlertType.BOOKING_CONFLICT,
        title="Schedule conflict",
        message=(
            f"⚠️ {first.provider_name} and {second.provider_name} overlap "
            f"around {second.start_time:%B %-d %H:%M}."
        ),
        requires_user_action=True,
    )


def check_departure(trip_state: TripState) -> Alert | None:
    """Scenario 3: is it time to leave for the next flight/train?"""
    next_event = find_next_event(trip_state)
    if next_event is None:
        return None
    lead = DEPARTURE_LEAD.get(next_event.booking_type)
    if lead is None:
        return None
    remaining = calculate_time_until_event(trip_state, next_event)
    if remaining > lead:
        return None
    destination = (
        "the airport"
        if next_event.booking_type == BookingType.FLIGHT
        else "the station"
    )
    return Alert(
        alert_type=AlertType.DEPARTURE_REQUIRED,
        title="Time to leave",
        message=(
            f"🔔 It is time to leave for {destination}. "
            f"{next_event.provider_name} departs at "
            f"{next_event.start_time:%H:%M} from {next_event.start_location}."
        ),
        requires_user_action=True,
    )


def check_free_time(trip_state: TripState) -> Alert | None:
    """Scenario 2: a large gap before the next event."""
    gap = detect_free_time(trip_state, threshold=FREE_TIME_THRESHOLD)
    if gap is None:
        return None
    next_event: BookingRecord = find_next_event(trip_state)  # type: ignore[assignment]
    hours = int(gap.total_seconds() // 3600)
    minutes = int((gap.total_seconds() % 3600) // 60)
    duration = f"{hours}h{minutes:02d}m" if minutes else f"{hours} hours"
    location = trip_state.current_location or next_event.start_location
    return Alert(
        alert_type=AlertType.FREE_TIME,
        title="Unexpected free time",
        message=(
            f"You have {duration} free in {location} until "
            f"{next_event.provider_name} at {next_event.start_time:%H:%M}."
        ),
        requires_user_action=False,
    )


def evaluate_trip(trip_state: TripState) -> list[Alert]:
    """Run all deterministic checks. Empty list == stay silent.

    Departure alerts suppress the free-time check: if the traveler must
    leave soon, the gap is not really free.
    """
    alerts: list[Alert] = []

    for check in (check_accommodation, check_conflicts, check_departure):
        alert = check(trip_state)
        if alert is not None:
            alerts.append(alert)

    if not any(a.alert_type == AlertType.DEPARTURE_REQUIRED for a in alerts):
        free_time = check_free_time(trip_state)
        if free_time is not None:
            alerts.append(free_time)

    return alerts
