"""Demo scenario setup, shared by the CLI runner and the web API.

This is demo tooling: it prepares a trip-state file for one of the three
required hackathon scenarios. The evaluation itself always runs through
the real business logic (decision_engine) — nothing here fakes outputs.
"""

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.models.booking import BookingRecord, BookingType
from app.storage.local_store import load_trip_state, save_trip_state

DEMO_DATA = Path(__file__).resolve().parents[2] / "data" / "demo_trip.json"


@dataclass(frozen=True)
class Scenario:
    key: str
    title: str
    current_time: datetime
    current_location: str
    resolve_gap: bool  # whether the Aug 19 gap is already fixed in this scenario


SCENARIOS: dict[str, Scenario] = {
    "conflict": Scenario(
        key="conflict",
        title="Booking conflict (missing hotel night)",
        current_time=datetime(2026, 8, 16, 9, 0),
        current_location="Zurich",
        resolve_gap=False,
    ),
    "freetime": Scenario(
        key="freetime",
        title="Unexpected free time in Zermatt",
        current_time=datetime(2026, 8, 18, 14, 0),
        current_location="Zermatt",
        resolve_gap=True,
    ),
    "airport": Scenario(
        key="airport",
        title="Airport departure alert",
        current_time=datetime(2026, 8, 22, 12, 30),
        current_location="Zurich",
        resolve_gap=True,
    ),
}

GAP_FIX_BOOKING = BookingRecord(
    booking_type=BookingType.HOTEL,
    provider_name="Hotel Matterhorn Focus",
    confirmation_number="HMF-2210",
    start_time=datetime(2026, 8, 19, 14, 0),
    end_time=datetime(2026, 8, 20, 10, 0),
    start_location="Zermatt",
    end_location="Zermatt",
)


def reset_state(path: Path) -> None:
    """Copy the pristine demo trip to the working state file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(DEMO_DATA, path)


def set_situation(path: Path, current_time: datetime, location: str) -> None:
    state = load_trip_state(path)
    state = state.model_copy(
        update={
            "current_time": current_time,
            "current_location": location,
            "updated_at": current_time,
        }
    )
    save_trip_state(state, path)


def resolve_accommodation_gap(path: Path) -> None:
    """Book the missing Aug 19 hotel night (scenario 1 resolution)."""
    state = load_trip_state(path)
    state.bookings.append(GAP_FIX_BOOKING.model_copy())
    state.bookings.sort(key=lambda booking: booking.start_time)
    save_trip_state(state, path)


def prepare_scenario(name: str, path: Path) -> Scenario:
    scenario = SCENARIOS[name]
    reset_state(path)
    set_situation(path, scenario.current_time, scenario.current_location)
    if scenario.resolve_gap:
        resolve_accommodation_gap(path)
    return scenario
