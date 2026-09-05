"""Web API: a thin layer over the existing business logic.

Every endpoint except /api/agent/run is deterministic and free.
/api/agent/run invokes the Strands agent on Amazon Bedrock (paid) and
is only called from an explicit button in the UI.
"""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.models.alert import Alert
from app.models.booking import BookingRecord
from app.models.trip_state import TripState
from app.services.decision_engine import evaluate_trip
from app.services.demo_scenarios import (
    SCENARIOS,
    prepare_scenario,
    reset_state,
    resolve_accommodation_gap,
    set_situation,
)
from app.storage.local_store import load_trip_state, save_trip_state
from app.tools import context

router = APIRouter(prefix="/api")

RUNTIME_STATE = Path(__file__).resolve().parents[2] / "data" / "runtime_trip.json"


def ensure_runtime_state() -> Path:
    if not RUNTIME_STATE.exists():
        reset_state(RUNTIME_STATE)
    context.set_trip_state_path(RUNTIME_STATE)
    return RUNTIME_STATE


class SituationUpdate(BaseModel):
    current_time: datetime
    current_location: str


class CheckResponse(BaseModel):
    trip: TripState
    alerts: list[Alert]
    silent: bool


def _check() -> CheckResponse:
    state = load_trip_state(ensure_runtime_state())
    alerts = evaluate_trip(state)
    return CheckResponse(trip=state, alerts=alerts, silent=not alerts)


@router.get("/trip", response_model=TripState)
def get_trip() -> TripState:
    return load_trip_state(ensure_runtime_state())


@router.get("/check", response_model=CheckResponse)
def check() -> CheckResponse:
    """Free deterministic monitoring pass."""
    return _check()


@router.post("/situation", response_model=CheckResponse)
def update_situation(update: SituationUpdate) -> CheckResponse:
    set_situation(ensure_runtime_state(), update.current_time, update.current_location)
    return _check()


@router.post("/scenario/{name}", response_model=CheckResponse)
def load_scenario(name: str) -> CheckResponse:
    if name not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"unknown scenario: {name}")
    prepare_scenario(name, ensure_runtime_state())
    return _check()


@router.post("/resolve-gap", response_model=CheckResponse)
def resolve_gap() -> CheckResponse:
    """Book the missing hotel night (scenario 1 resolution)."""
    resolve_accommodation_gap(ensure_runtime_state())
    return _check()


@router.post("/reset", response_model=CheckResponse)
def reset() -> CheckResponse:
    reset_state(ensure_runtime_state())
    return _check()


class AgentRunRequest(BaseModel):
    message: str | None = None


class AgentRunResponse(BaseModel):
    final_text: str
    notifications: list[Alert]
    trip: TripState


@router.post("/agent/run", response_model=AgentRunResponse)
def agent_run(payload: AgentRunRequest | None = None) -> AgentRunResponse:
    """Run the Strands agent on Bedrock (PAID).

    Without a message: one autonomous monitoring cycle.
    With a message: handle a traveler-initiated request (the agent may
    update the trip state, search the web, and reply).
    """
    path = ensure_runtime_state()
    from app.agent.travel_agent import (
        build_travel_agent,
        run_monitoring_cycle,
        run_user_request,
    )
    from app.tools.notification_tools import sent_alerts

    message = (payload.message or "").strip() if payload else ""
    sent_alerts.clear()
    try:
        agent = build_travel_agent()
        if message:
            result = run_user_request(agent, message)
        else:
            result = run_monitoring_cycle(agent)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Bedrock call failed: {exc}") from exc
    return AgentRunResponse(
        final_text=str(result).strip(),
        notifications=list(sent_alerts),
        trip=load_trip_state(path),
    )


MAX_IMPORT_BYTES = 8 * 1024 * 1024

_EXTENSION_FORMATS = {
    ".png": "png", ".jpg": "jpeg", ".jpeg": "jpeg",
    ".webp": "webp", ".gif": "gif", ".pdf": "pdf",
}


class ImportResponse(BaseModel):
    added: list[BookingRecord]
    skipped_duplicates: int
    check: CheckResponse


def _add_bookings(new_bookings: list[BookingRecord]) -> ImportResponse:
    path = ensure_runtime_state()
    state = load_trip_state(path)
    existing_numbers = {
        b.confirmation_number for b in state.bookings if b.confirmation_number
    }
    added: list[BookingRecord] = []
    skipped = 0
    for booking in new_bookings:
        if booking.confirmation_number and booking.confirmation_number in existing_numbers:
            skipped += 1
            continue
        state.bookings.append(booking)
        added.append(booking)
    state.bookings.sort(key=lambda b: b.start_time)
    save_trip_state(state, path)
    return ImportResponse(added=added, skipped_duplicates=skipped, check=_check())


@router.post("/bookings/import", response_model=ImportResponse)
async def import_bookings(
    file: UploadFile | None = File(None),  # noqa: B008 (FastAPI idiom)
    text: str | None = Form(None),
) -> ImportResponse:
    """Extract bookings from a dropped file or pasted text (PAID: one
    Bedrock call), then add them to the trip.

    Files: .eml / .txt are read as text; .pdf and images (png, jpg, webp,
    gif) are sent to the model directly.
    """
    from app.services.booking_extractor import (
        eml_to_text,
        extract_bookings,
        extract_bookings_from_file,
    )

    try:
        if file is not None:
            data = await file.read()
            if len(data) > MAX_IMPORT_BYTES:
                raise HTTPException(status_code=413, detail="File is too large (max 8 MB).")
            name = (file.filename or "").lower()
            suffix = name[name.rfind("."):] if "." in name else ""
            if suffix in _EXTENSION_FORMATS:
                bookings = extract_bookings_from_file(data, _EXTENSION_FORMATS[suffix])
            elif suffix == ".eml":
                bookings = extract_bookings(eml_to_text(data))
            elif suffix in (".txt", ".md", ""):
                bookings = extract_bookings(data.decode("utf-8", errors="replace"))
            else:
                raise HTTPException(
                    status_code=415,
                    detail=f"Unsupported file type: {suffix or 'unknown'}. "
                    "Use .eml, .txt, .pdf, or an image.",
                )
        elif text and text.strip():
            bookings = extract_bookings(text.strip())
        else:
            raise HTTPException(status_code=422, detail="Provide a file or text.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Extraction failed: {exc}") from exc

    if not bookings:
        raise HTTPException(status_code=422, detail="No bookings found in the input.")
    return _add_bookings(bookings)


class PlanResponse(BaseModel):
    plan: str


@router.post("/plan", response_model=PlanResponse)
def generate_plan() -> PlanResponse:
    """Generate today's plan (PAID: one Bedrock call).

    Refused with 409 while the trip has unresolved conflicts — the agent
    never plans on top of a broken itinerary.
    """
    from app.services.itinerary_generator import (
        ItineraryBlockedError,
        generate_day_plan,
    )

    state = load_trip_state(ensure_runtime_state())
    try:
        plan = generate_day_plan(state)
    except ItineraryBlockedError as exc:
        raise HTTPException(
            status_code=409,
            detail="Itinerary generation is blocked until conflicts are "
            f"resolved: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Bedrock call failed: {exc}") from exc
    return PlanResponse(plan=plan)
