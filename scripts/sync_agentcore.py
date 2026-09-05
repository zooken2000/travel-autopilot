"""Sync the project sources into agentcore_runtime/ before a deploy.

The AgentCore Runtime bundle (CodeZip of agentcore_runtime/) must be
self-contained, so this copies the `app` package and the demo trip data
next to the runtime entrypoint. Run before every `agentcore deploy`.
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "agentcore_runtime"


def main() -> None:
    for name in ("app", "data"):
        target = RUNTIME / name
        if target.exists():
            shutil.rmtree(target)
    shutil.copytree(ROOT / "app", RUNTIME / "app",
                    ignore=shutil.ignore_patterns("__pycache__", "*.egg-info", "api"))
    (RUNTIME / "data").mkdir()
    shutil.copy(ROOT / "data" / "demo_trip.json", RUNTIME / "data" / "demo_trip.json")
    print(f"synced app/ and data/demo_trip.json into {RUNTIME}")


if __name__ == "__main__":
    main()
