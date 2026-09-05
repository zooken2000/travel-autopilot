from datetime import datetime
from pathlib import Path

from app.agent.travel_agent import (
    TRAVEL_AGENT_TOOLS,
    build_travel_agent,
    format_findings,
    load_system_prompt,
)
from app.models.trip_state import TripState
from app.storage.local_store import load_trip_state


def test_system_prompt_loads() -> None:
    prompt = load_system_prompt()
    assert "Travel Autopilot" in prompt
    assert "Silence is preferred" in prompt


def test_agent_builds_with_five_tools() -> None:
    agent = build_travel_agent()
    assert len(TRAVEL_AGENT_TOOLS) == 5
    for name in (
        "get_trip_state",
        "update_trip_state",
        "check_next_event",
        "search_web",
        "notify_user",
    ):
        assert name in agent.tool_names


def test_format_findings_reports_demo_issues() -> None:
    state = load_trip_state(Path("data/demo_trip.json"))
    findings = format_findings(state)
    assert "No accommodation found for August 19" in findings
    assert "free" in findings.lower()  # 14:00 -> 19:00 dinner gap


def test_format_findings_silent_when_all_well() -> None:
    state = TripState(
        trip_id="quiet",
        current_time=datetime(2026, 8, 16, 10, 0),
        bookings=[],
        updated_at=datetime(2026, 8, 16, 10, 0),
    )
    assert "No issues detected" in format_findings(state)


def test_user_request_prompt_contains_message_and_findings() -> None:
    from app.agent.travel_agent import build_user_request_prompt

    prompt = build_user_request_prompt(
        "Finished early, I'm at Gornergrat", "- No issues detected."
    )
    assert "Gornergrat" in prompt
    assert "No issues detected" in prompt
    assert "update_trip_state" in prompt
