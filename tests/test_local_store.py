from pathlib import Path

from app.models.trip_state import TripState
from app.storage.local_store import load_trip_state, save_trip_state


def test_demo_trip_loads() -> None:
    state = load_trip_state(Path("data/demo_trip.json"))
    assert isinstance(state, TripState)
    assert state.trip_id == "swiss-2026-08"
    assert len(state.bookings) == 7


def test_round_trip(tmp_path: Path) -> None:
    state = load_trip_state(Path("data/demo_trip.json"))
    out = tmp_path / "trip.json"
    save_trip_state(state, out)
    assert load_trip_state(out) == state
