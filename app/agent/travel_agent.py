"""The Travel Autopilot agent (Strands Agents SDK + Amazon Bedrock).

The agent's job is judgment: whether the traveler needs to be
interrupted, and whether fresh external information is required.
All facts (times, gaps, conflicts) come from deterministic services.
"""

import os
from pathlib import Path

from strands import Agent
from strands.models import BedrockModel

from app.models.trip_state import TripState
from app.services.decision_engine import evaluate_trip
from app.storage.local_store import load_trip_state
from app.tools.context import get_trip_state_path
from app.tools.itinerary_tools import (
    check_next_event,
    get_trip_state,
    update_trip_state,
)
from app.tools.notification_tools import notify_user
from app.tools.web_search_tools import search_web

_SYSTEM_PROMPT_PATH = Path(__file__).parent / "system_prompt.md"

TRAVEL_AGENT_TOOLS = [
    get_trip_state,
    update_trip_state,
    check_next_event,
    search_web,
    notify_user,
]

_MONITORING_PROMPT = """\
Run one monitoring cycle for the current trip.

Deterministic checks have already been computed:
{findings}

Your task:
1. Read the trip state with get_trip_state.
2. Decide whether the traveler truly needs to be interrupted.
3. If a finding needs current external information to be useful
   (e.g. suggesting activities for free time), use search_web first.
4. If intervention is required, call notify_user with a concise,
   actionable message. One notification per distinct issue.
5. If nothing requires attention, do NOT call notify_user; reply with
   exactly: SILENT

Never invent problems. Never notify about things that are fine.
"""


def load_system_prompt() -> str:
    return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def build_travel_agent(model_id: str | None = None) -> Agent:
    """Create the Travel Autopilot agent with its five tools."""
    model = BedrockModel(
        model_id=model_id
        or os.environ.get(
            "BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
        ),
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
        temperature=0.2,
    )
    return Agent(
        model=model,
        system_prompt=load_system_prompt(),
        tools=TRAVEL_AGENT_TOOLS,
    )


def format_findings(trip_state: TripState) -> str:
    """Render deterministic findings for the monitoring prompt."""
    alerts = evaluate_trip(trip_state)
    if not alerts:
        return "- No issues detected. Everything is on schedule."
    return "\n".join(
        f"- [{alert.alert_type.value}] {alert.title}: {alert.message}"
        for alert in alerts
    )


_USER_REQUEST_PROMPT = """\
The traveler sent you a message:

"{message}"

Deterministic checks on the current trip state:
{findings}

Your task:
1. Read the trip state with get_trip_state.
2. If the traveler reports a change in their situation (an event finished
   early, they moved to another location, they want to skip something),
   FIRST update the trip state with update_trip_state so it reflects
   reality — including current_time and current_location when mentioned.
3. Use search_web when the request needs current local information
   (activities, opening hours, transport options).
4. Answer the traveler directly with a concise, actionable reply that
   respects the itinerary (never suggest something that would make them
   miss the next event). Use notify_user only for urgent issues beyond
   their question.
"""


def build_user_request_prompt(message: str, findings: str) -> str:
    return _USER_REQUEST_PROMPT.format(message=message, findings=findings)


def run_user_request(agent: Agent, message: str) -> str:
    """Handle a traveler-initiated request (e.g. "finished early, I'm at
    Gornergrat — any suggestions?")."""
    trip_state = load_trip_state(get_trip_state_path())
    findings = format_findings(trip_state)
    result = agent(build_user_request_prompt(message, findings))
    return str(result)


def run_monitoring_cycle(agent: Agent) -> str:
    """One pass of the autonomous loop: observe → decide → (notify | silence)."""
    trip_state = load_trip_state(get_trip_state_path())
    findings = format_findings(trip_state)
    result = agent(_MONITORING_PROMPT.format(findings=findings))
    return str(result)
