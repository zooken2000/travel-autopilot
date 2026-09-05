import json
from datetime import datetime
from pathlib import Path

from app.models.trip_state import TripState
from app.storage.local_store import load_trip_state
from app.tools import context
from app.tools.itinerary_tools import (
    check_next_event,
    get_trip_state,
    update_trip_state,
)
from app.tools.notification_tools import notify_user, sent_alerts


def _setup_state(tmp_path: Path) -> Path:
    source = Path("data/demo_trip.json").read_text(encoding="utf-8")
    path = tmp_path / "trip.json"
    path.write_text(source, encoding="utf-8")
    context.set_trip_state_path(path)
    return path


def test_get_trip_state_returns_valid_json(tmp_path: Path) -> None:
    _setup_state(tmp_path)
    state = TripState.model_validate_json(get_trip_state())
    assert state.trip_id == "swiss-2026-08"


def test_check_next_event_reports_dinner(tmp_path: Path) -> None:
    _setup_state(tmp_path)
    result = check_next_event()
    assert "Whymper-Stube" in result
    assert "5h00m" in result


def test_update_trip_state_add_and_remove(tmp_path: Path) -> None:
    path = _setup_state(tmp_path)
    update = {
        "remove_confirmation_numbers": ["HBZ-1107"],
        "add_bookings": [
            {
                "booking_type": "hotel",
                "provider_name": "Hotel Matterhorn Extra Night",
                "start_time": "2026-08-19T14:00:00",
                "end_time": "2026-08-20T10:00:00",
                "start_location": "Zermatt",
                "end_location": "Zermatt",
            }
        ],
        "current_location": "Zermatt",
    }
    result = update_trip_state(json.dumps(update))
    assert "updated" in result

    state = load_trip_state(path)
    providers = [b.provider_name for b in state.bookings]
    assert "Hotel Matterhorn Extra Night" in providers
    assert all(b.confirmation_number != "HBZ-1107" for b in state.bookings)
    # bookings stay sorted by start time
    assert state.bookings == sorted(state.bookings, key=lambda b: b.start_time)


def test_update_trip_state_sets_current_time(tmp_path: Path) -> None:
    path = _setup_state(tmp_path)
    update_trip_state(json.dumps({"current_time": "2026-08-22T12:30:00"}))
    assert load_trip_state(path).current_time == datetime(2026, 8, 22, 12, 30)


def test_notify_user_records_alert() -> None:
    sent_alerts.clear()
    result = notify_user(
        alert_type="departure_required",
        title="Time to leave",
        message="It is time to leave for the airport.",
    )
    assert "delivered" in result
    assert len(sent_alerts) == 1
    assert sent_alerts[0].requires_user_action is True
