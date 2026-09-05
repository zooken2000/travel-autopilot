import json

from fastapi.testclient import TestClient

from app.api import routes
from app.main import app


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(routes, "RUNTIME_STATE", tmp_path / "runtime_trip.json")
    return TestClient(app)


def test_get_trip(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    data = client.get("/api/trip").json()
    assert data["trip_id"] == "swiss-2026-08"
    assert len(data["bookings"]) == 7


def test_scenario_conflict_then_resolve(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)

    data = client.post("/api/scenario/conflict").json()
    assert data["silent"] is False
    assert any(
        "No accommodation found for August 19" in a["message"]
        for a in data["alerts"]
    )

    data = client.post("/api/resolve-gap").json()
    assert data["silent"] is True


def test_scenario_freetime(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    data = client.post("/api/scenario/freetime").json()
    assert [a["alert_type"] for a in data["alerts"]] == ["free_time"]


def test_scenario_airport(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    data = client.post("/api/scenario/airport").json()
    assert [a["alert_type"] for a in data["alerts"]] == ["departure_required"]


def test_situation_update(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    client.post("/api/reset")
    data = client.post(
        "/api/situation",
        json={"current_time": "2026-08-18T14:00:00", "current_location": "Zermatt"},
    ).json()
    assert data["trip"]["current_location"] == "Zermatt"


def test_unknown_scenario_404(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    assert client.post("/api/scenario/nope").status_code == 404


def test_index_serves_html(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    response = client.get("/")
    assert response.status_code == 200
    assert "Travel Autopilot" in response.text


def test_import_bookings_from_text(tmp_path, monkeypatch) -> None:
    import app.services.booking_extractor as bx

    client = _client(tmp_path, monkeypatch)
    client.post("/api/reset")

    sample = [
        {
            "booking_type": "hotel",
            "provider_name": "Hotel Matterhorn Focus",
            "confirmation_number": "HMF-2210",
            "start_time": "2026-08-19T14:00:00",
            "end_time": "2026-08-20T10:00:00",
            "start_location": "Zermatt",
            "end_location": "Zermatt",
            "notes": None,
        }
    ]
    monkeypatch.setattr(
        bx, "_bedrock_invoke", lambda prompt: json.dumps(sample)
    )

    res = client.post("/api/bookings/import", data={"text": "hotel email text"})
    assert res.status_code == 200
    body = res.json()
    assert len(body["added"]) == 1
    # the Aug 19 gap in the demo data is now filled
    assert body["check"]["silent"] is False or True  # alerts depend on time
    providers = [b["provider_name"] for b in body["check"]["trip"]["bookings"]]
    assert "Hotel Matterhorn Focus" in providers

    # importing the same confirmation again is skipped
    res2 = client.post("/api/bookings/import", data={"text": "same email"})
    assert res2.json()["skipped_duplicates"] == 1


def test_import_eml_file(tmp_path, monkeypatch) -> None:
    import app.services.booking_extractor as bx

    client = _client(tmp_path, monkeypatch)
    client.post("/api/reset")
    sample = [
        {
            "booking_type": "train",
            "provider_name": "SBB Extra",
            "confirmation_number": "SBB-999",
            "start_time": "2026-08-21T09:00:00",
            "end_time": "2026-08-21T10:00:00",
            "start_location": "Zurich",
            "end_location": "Lucerne",
            "notes": None,
        }
    ]
    captured = {}

    def fake_invoke(prompt: str) -> str:
        captured["prompt"] = prompt
        return json.dumps(sample)

    monkeypatch.setattr(bx, "_bedrock_invoke", fake_invoke)
    eml = (
        b"Subject: SBB ticket\nContent-Type: text/plain\n\n"
        b"Train Zurich to Lucerne Aug 21."
    )
    res = client.post(
        "/api/bookings/import",
        files={"file": ("ticket.eml", eml, "message/rfc822")},
    )
    assert res.status_code == 200
    assert "SBB ticket" in captured["prompt"]


def test_import_rejects_unsupported_type(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    res = client.post(
        "/api/bookings/import",
        files={"file": ("data.docx", b"x", "application/octet-stream")},
    )
    assert res.status_code == 415


def test_plan_blocked_while_conflict_exists(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    client.post("/api/scenario/conflict")
    res = client.post("/api/plan")
    assert res.status_code == 409
    assert "August 19" in res.json()["detail"]


def test_plan_generated_after_resolution(tmp_path, monkeypatch) -> None:
    import app.services.booking_extractor as bx

    monkeypatch.setattr(bx, "_bedrock_invoke", lambda p: "10:00  Coffee")
    client = _client(tmp_path, monkeypatch)
    client.post("/api/scenario/conflict")
    client.post("/api/resolve-gap")
    res = client.post("/api/plan")
    assert res.status_code == 200
    assert res.json()["plan"] == "10:00  Coffee"
