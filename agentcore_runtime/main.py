"""AgentCore Runtime entrypoint for Travel Autopilot.

The `app/` package and `data/` here are synced copies of the project
sources — regenerate them with `python scripts/sync_agentcore.py`
before every deploy.
"""

import shutil
from pathlib import Path

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from app.agent.travel_agent import build_travel_agent, run_monitoring_cycle, run_user_request
from app.tools import context
from app.tools.notification_tools import sent_alerts

app = BedrockAgentCoreApp()

# The code bundle is read-only at runtime; keep mutable trip state in /tmp.
_BUNDLED_TRIP = Path(__file__).parent / "data" / "demo_trip.json"
_RUNTIME_TRIP = Path("/tmp/trip.json")
if not _RUNTIME_TRIP.exists():
    shutil.copy(_BUNDLED_TRIP, _RUNTIME_TRIP)
context.set_trip_state_path(_RUNTIME_TRIP)

_agent = build_travel_agent()


@app.entrypoint
def invoke(payload):
    """prompt empty or 'monitor' → autonomous monitoring cycle;
    anything else → traveler request."""
    prompt = (payload.get("prompt") or "").strip() if isinstance(payload, dict) else ""
    sent_alerts.clear()
    if prompt and prompt.lower() != "monitor":
        result = run_user_request(_agent, prompt)
    else:
        result = run_monitoring_cycle(_agent)
    return {
        "result": str(result).strip(),
        "notifications": [alert.model_dump() for alert in sent_alerts],
    }


if __name__ == "__main__":
    app.run()
