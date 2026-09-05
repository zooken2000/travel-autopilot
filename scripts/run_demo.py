"""Run the three required demo scenarios through the real business logic.

Default mode exercises the deterministic pipeline (no AWS needed).
--agent additionally runs the full Strands agent on Amazon Bedrock.

Usage:
    python scripts/run_demo.py [conflict|freetime|airport] [--agent]
"""

import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.decision_engine import evaluate_trip  # noqa: E402
from app.services.demo_scenarios import (  # noqa: E402
    SCENARIOS,
    prepare_scenario,
    resolve_accommodation_gap,
)
from app.storage.local_store import load_trip_state  # noqa: E402
from app.tools import context  # noqa: E402


def _print_alerts(path: Path) -> None:
    state = load_trip_state(path)
    alerts = evaluate_trip(state)
    print(f"  current time : {state.current_time:%Y-%m-%d %H:%M}")
    print(f"  location     : {state.current_location}")
    if not alerts:
        print("  → (silence) no intervention required ✓")
        return
    for alert in alerts:
        marker = "action required" if alert.requires_user_action else "fyi"
        print(f"  → [{alert.alert_type.value} / {marker}] {alert.message}")


def _run_agent() -> None:
    from app.agent.travel_agent import build_travel_agent, run_monitoring_cycle
    from app.tools.notification_tools import sent_alerts

    print("\n  --- Strands agent (Amazon Bedrock) ---")
    agent = build_travel_agent()
    sent_alerts.clear()
    result = run_monitoring_cycle(agent)
    text = str(result).strip()
    if text and text != "SILENT":
        print(f"\n  agent final message: {text[:2000]}")
    if sent_alerts:
        print(f"  → agent sent {len(sent_alerts)} notification(s) ✓")
    else:
        print("  → agent stayed silent (no notifications) ✓")


def run_scenario(name: str, agent_mode: bool) -> None:
    scenario = SCENARIOS[name]
    workdir = Path(tempfile.mkdtemp(prefix="travel-autopilot-"))
    path = workdir / "trip.json"
    prepare_scenario(name, path)
    context.set_trip_state_path(path)

    print(f"\n=== Scenario: {scenario.title} ===")
    _print_alerts(path)

    if name == "conflict":
        print("\n  Itinerary generation is blocked until the conflict is resolved.")
        print("  ...resolving: booking a Zermatt hotel for the night of Aug 19...\n")
        resolve_accommodation_gap(path)
        _print_alerts(path)

    if agent_mode:
        _run_agent()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "scenario", nargs="?", choices=[*SCENARIOS, "all"], default="all"
    )
    parser.add_argument(
        "--agent",
        action="store_true",
        help="also run the full Strands agent on Amazon Bedrock",
    )
    args = parser.parse_args()

    names = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
    for name in names:
        run_scenario(name, args.agent)
    print()


if __name__ == "__main__":
    main()
