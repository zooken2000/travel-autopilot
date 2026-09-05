"""Extract structured BookingRecords from booking confirmations.

Accepts plain text (pasted email), .eml files, and — via Bedrock's
multimodal Converse API — PDF confirmations and screenshots directly.
Every LLM call is isolated behind an injectable callable so parsing and
validation stay fully testable without Bedrock.
"""

import email
import json
import os
import re
from collections.abc import Callable
from email import policy

from pydantic import TypeAdapter

from app.models.booking import BookingRecord

_EXTRACTION_RULES = """\
You extract travel bookings from booking confirmations (emails, PDFs,
screenshots, notes).

Return ONLY a JSON array. Each element must have exactly these keys:
- booking_type: one of "flight", "hotel", "train", "activity", "other"
- provider_name: string
- confirmation_number: string or null
- start_time: ISO 8601 datetime (for hotels: check-in)
- end_time: ISO 8601 datetime (for hotels: check-out)
- start_location: string
- end_location: string (for hotels: same as start_location)
- notes: string or null

Rules:
- Do not invent bookings that are not in the source.
- If a year is missing, assume the current trip year from context.
- Output the JSON array only, with no markdown fences and no commentary.
"""

_TEXT_PROMPT = _EXTRACTION_RULES + """
Booking text:
---
{raw_text}
---
"""

_FILE_PROMPT = _EXTRACTION_RULES + """
Extract the bookings from the attached file.
"""

# formats Bedrock Converse accepts for image / document blocks
IMAGE_FORMATS = {"png", "jpeg", "webp", "gif"}
DOCUMENT_FORMATS = {"pdf"}

_bookings_adapter = TypeAdapter(list[BookingRecord])


def _model_id() -> str:
    return os.environ.get(
        "BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
    )


def _client():
    import boto3

    return boto3.client(
        "bedrock-runtime",
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
    )


def _converse(content: list[dict]) -> str:
    response = _client().converse(
        modelId=_model_id(),
        messages=[{"role": "user", "content": content}],
        inferenceConfig={"maxTokens": 4096, "temperature": 0.0},
    )
    return response["output"]["message"]["content"][0]["text"]


def _bedrock_invoke(prompt: str) -> str:
    return _converse([{"text": prompt}])


def _bedrock_invoke_file(prompt: str, data: bytes, file_format: str) -> str:
    if file_format in DOCUMENT_FORMATS:
        block = {
            "document": {
                "format": file_format,
                "name": "booking-confirmation",
                "source": {"bytes": data},
            }
        }
    else:
        block = {"image": {"format": file_format, "source": {"bytes": data}}}
    return _converse([block, {"text": prompt}])


def _parse_output(output: str, raw_source_text: str | None) -> list[BookingRecord]:
    """Tolerate models that wrap output in ```json fences anyway."""
    match = re.search(r"\[.*\]", output, re.DOTALL)
    parsed = json.loads(match.group(0) if match else output)
    bookings = _bookings_adapter.validate_python(parsed)
    for booking in bookings:
        booking.raw_source_text = raw_source_text
    return bookings


def eml_to_text(data: bytes) -> str:
    """Flatten an .eml file to plain text for extraction."""
    message = email.message_from_bytes(data, policy=policy.default)
    body = message.get_body(preferencelist=("plain", "html"))
    text = body.get_content() if body else ""
    if body is not None and body.get_content_type() == "text/html":
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s{2,}", " ", text)
    header = "\n".join(
        f"{name}: {message[name]}" for name in ("Subject", "From", "Date")
        if message[name]
    )
    return f"{header}\n\n{text}".strip()


def extract_bookings(
    raw_text: str,
    invoke: Callable[[str], str] | None = None,
) -> list[BookingRecord]:
    """Unstructured booking text → validated BookingRecords."""
    call = invoke or _bedrock_invoke
    output = call(_TEXT_PROMPT.format(raw_text=raw_text))
    return _parse_output(output, raw_text)


def extract_bookings_from_file(
    data: bytes,
    file_format: str,
    invoke: Callable[[str, bytes, str], str] | None = None,
) -> list[BookingRecord]:
    """PDF or screenshot bytes → validated BookingRecords.

    file_format: one of png, jpeg, webp, gif, pdf.
    """
    if file_format not in IMAGE_FORMATS | DOCUMENT_FORMATS:
        raise ValueError(f"unsupported file format: {file_format}")
    call = invoke or _bedrock_invoke_file
    output = call(_FILE_PROMPT, data, file_format)
    return _parse_output(output, f"(uploaded {file_format} file)")
