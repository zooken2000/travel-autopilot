"""Day-plan generation.

Deterministic logic decides WHETHER a plan may be generated (blocked
while the trip has unresolved conflicts — per spec, the agent must not
plan on top of a broken itinerary). The LLM only writes the plan text.
"""

from collections.abc import Callable

from app.models.alert import Alert
from app.models.trip_state import TripState
from app.services.decision_engine import check_accommodation, check_conflicts


class ItineraryBlockedError(Exception):
    """Raised when unresolved conflicts prevent plan generation."""

    def __init__(self, alerts: list[Alert]):
        self.alerts = alerts
        super().__init__("; ".join(a.message for a in alerts))


_PLAN_PROMPT = """\
You are a travel planner. Write a concise plan for the traveler's day.

Current time: {current_time}
Current location: {current_location}

Today's fixed commitments (must be kept, never rescheduled):
{events}

Rules:
- Build the plan around the fixed commitments; leave sensible buffers
  for transfers and meals.
- Suggest at most 2-3 optional activities that fit the location and the
  gaps; do not overfill the day.
- Plain text, one line per time slot, e.g. "14:00  Walk to the Matterhorn
  viewpoint (20 min)". No markdown, no commentary before or after.
"""


def blocking_alerts(trip_state: TripState) -> list[Alert]:
    """Conflicts that must be resolved before planning is allowed."""
    return [
        alert
        for alert in (check_accommodation(trip_state), check_conflicts(trip_state))
        if alert is not None
    ]


def build_plan_prompt(trip_state: TripState) -> str:
    today = trip_state.current_time.date()
    events = [
        f"- {b.start_time:%H:%M}-{b.end_time:%H:%M} {b.booking_type.value}: "
        f"{b.provider_name} ({b.start_location} → {b.end_location})"
        for b in sorted(trip_state.bookings, key=lambda b: b.start_time)
        if b.start_time.date() == today or b.end_time.date() == today
    ]
    return _PLAN_PROMPT.format(
        current_time=f"{trip_state.current_time:%Y-%m-%d %H:%M}",
        current_location=trip_state.current_location or "(infer from itinerary)",
        events="\n".join(events) or "- (no fixed commitments today)",
    )


def generate_day_plan(
    trip_state: TripState,
    invoke: Callable[[str], str] | None = None,
) -> str:
    """Generate today's plan, or raise ItineraryBlockedError.

    `invoke` defaults to a Bedrock call; inject a fake in tests.
    """
    blockers = blocking_alerts(trip_state)
    if blockers:
        raise ItineraryBlockedError(blockers)

    if invoke is None:
        from app.services.booking_extractor import _bedrock_invoke

        invoke = _bedrock_invoke
    return invoke(build_plan_prompt(trip_state)).strip()
