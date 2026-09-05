"""Trip-state tools exposed to the Strands agent.

The tools are thin: all real logic lives in deterministic services and
Pydantic validation, so it stays testable without an LLM.
"""

from datetime import datetime

from pydantic import BaseModel
from strands import tool

from app.models.booking import BookingRecord
from app.models.trip_state import TripState
from app.services.trip_monitor import calculate_time_until_event, find_next_event
from app.storage.local_store import load_trip_state, save_trip_state
from app.tools.context import get_trip_state_path


class TripStateUpdate(BaseModel):
    """A validated, declarative update to the trip state.

    The agent describes WHAT changes; applying it is deterministic.
    """

    add_bookings: list[BookingRecord] = []
    remove_confirmation_numbers: list[str] = []
    remove_provider_names: list[str] = []
    current_location: str | None = None
    current_time: datetime | None = None


def apply_update(trip_state: TripState, update: TripStateUpdate) -> TripState:
    """Pure function: apply an update and return the new state."""
    bookings = [
        booking
        for booking in trip_state.bookings
        if booking.confirmation_number not in update.remove_confirmation_numbers
        and booking.provider_name not in update.remove_provider_names
    ]
    bookings.extend(update.add_bookings)
    bookings.sort(key=lambda booking: booking.start_time)

    return trip_state.model_copy(
        update={
            "bookings": bookings,
            "current_location": update.current_location
            or trip_state.current_location,
            "current_time": update.current_time or trip_state.current_time,
            "updated_at": update.current_time or trip_state.current_time,
        }
    )


@tool
def get_trip_state() -> str:
    """Return the current trip state (itinerary, bookings, current time and
    location) as JSON. Read this before making any decision."""
    return load_trip_state(get_trip_state_path()).model_dump_json(indent=2)


@tool
def update_trip_state(update_json: str) -> str:
    """Update the trip state so it always reflects the CURRENT plan.

    Pass a JSON object with any of these keys:
    - "add_bookings": list of booking objects (booking_type, provider_name,
      start_time, end_time, start_location, end_location, ...)
    - "remove_confirmation_numbers": list of confirmation numbers to drop
    - "remove_provider_names": list of provider names to drop
    - "current_location": new current location string
    - "current_time": new current time (ISO 8601)
    """
    update = TripStateUpdate.model_validate_json(update_json)
    path = get_trip_state_path()
    new_state = apply_update(load_trip_state(path), update)
    save_trip_state(new_state, path)
    return (
        f"Trip state updated: {len(new_state.bookings)} bookings, "
        f"current location {new_state.current_location}, "
        f"current time {new_state.current_time:%Y-%m-%d %H:%M}."
    )


@tool
def check_next_event() -> str:
    """Return the next upcoming event and how much time remains until it."""
    trip_state = load_trip_state(get_trip_state_path())
    next_event = find_next_event(trip_state)
    if next_event is None:
        return "No upcoming events in the itinerary."
    remaining = calculate_time_until_event(trip_state, next_event)
    hours, rest = divmod(int(remaining.total_seconds()), 3600)
    minutes = rest // 60
    return (
        f"Next event: {next_event.booking_type.value} — "
        f"{next_event.provider_name} at {next_event.start_time:%Y-%m-%d %H:%M} "
        f"({next_event.start_location} → {next_event.end_location}). "
        f"Time remaining: {hours}h{minutes:02d}m."
    )
