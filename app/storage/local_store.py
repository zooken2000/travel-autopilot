"""Local JSON persistence for TripState (MVP storage)."""

from pathlib import Path

from app.models.trip_state import TripState


def load_trip_state(path: Path) -> TripState:
    return TripState.model_validate_json(path.read_text(encoding="utf-8"))


def save_trip_state(trip_state: TripState, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(trip_state.model_dump_json(indent=2), encoding="utf-8")
