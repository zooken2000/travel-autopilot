import json

import pytest

from app.models.booking import BookingType
from app.services.booking_extractor import extract_bookings

_SAMPLE_OUTPUT = json.dumps(
    [
        {
            "booking_type": "flight",
            "provider_name": "Swiss International Air Lines",
            "confirmation_number": "ABC123",
            "start_time": "2026-08-22T15:55:00",
            "end_time": "2026-08-23T10:25:00",
            "start_location": "Zurich (ZRH)",
            "end_location": "Tokyo Narita (NRT)",
            "notes": None,
        }
    ]
)


def test_extract_bookings_with_clean_json() -> None:
    bookings = extract_bookings("some email text", invoke=lambda prompt: _SAMPLE_OUTPUT)

    assert len(bookings) == 1
    assert bookings[0].booking_type == BookingType.FLIGHT
    assert bookings[0].confirmation_number == "ABC123"
    assert bookings[0].raw_source_text == "some email text"


def test_extract_bookings_tolerates_markdown_fences() -> None:
    fenced = f"```json\n{_SAMPLE_OUTPUT}\n```"
    bookings = extract_bookings("text", invoke=lambda prompt: fenced)
    assert len(bookings) == 1


def test_extract_bookings_rejects_invalid_schema() -> None:
    from pydantic import ValidationError

    bad = json.dumps([{"booking_type": "flight"}])
    with pytest.raises(ValidationError):
        extract_bookings("text", invoke=lambda prompt: bad)


def test_prompt_contains_raw_text() -> None:
    captured: dict[str, str] = {}

    def fake_invoke(prompt: str) -> str:
        captured["prompt"] = prompt
        return _SAMPLE_OUTPUT

    extract_bookings("LX160 Zurich to Tokyo", invoke=fake_invoke)
    assert "LX160 Zurich to Tokyo" in captured["prompt"]


_SAMPLE_EML = b"""\
Subject: Your booking HMF-2210
From: reservations@example.com
Date: Sat, 15 Aug 2026 10:00:00 +0200
Content-Type: text/plain; charset="utf-8"

Hotel Matterhorn Focus, Zermatt
Check-in Aug 19 2026 14:00, check-out Aug 20 2026 10:00.
"""


def test_eml_to_text_includes_subject_and_body() -> None:
    from app.services.booking_extractor import eml_to_text

    text = eml_to_text(_SAMPLE_EML)
    assert "Your booking HMF-2210" in text
    assert "Hotel Matterhorn Focus" in text


def test_extract_bookings_from_file_with_mock() -> None:
    from app.services.booking_extractor import extract_bookings_from_file

    captured = {}

    def fake_invoke(prompt: str, data: bytes, file_format: str) -> str:
        captured["format"] = file_format
        captured["bytes"] = data
        return _SAMPLE_OUTPUT

    bookings = extract_bookings_from_file(b"binary", "png", invoke=fake_invoke)
    assert captured["format"] == "png"
    assert len(bookings) == 1
    assert bookings[0].raw_source_text == "(uploaded png file)"


def test_extract_bookings_from_file_rejects_unknown_format() -> None:
    from app.services.booking_extractor import extract_bookings_from_file

    with pytest.raises(ValueError):
        extract_bookings_from_file(b"x", "docx", invoke=lambda *a: "[]")
