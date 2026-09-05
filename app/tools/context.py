"""Shared runtime context for agent tools: where the trip state lives."""

from pathlib import Path

_DEFAULT_PATH = Path("data/demo_trip.json")
_trip_state_path: Path = _DEFAULT_PATH


def set_trip_state_path(path: Path) -> None:
    global _trip_state_path
    _trip_state_path = path


def get_trip_state_path() -> Path:
    return _trip_state_path
