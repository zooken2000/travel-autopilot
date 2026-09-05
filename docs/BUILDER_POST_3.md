# builder.aws.com Post 3 Draft (bonus)

**Title:** Agents for Humans: Turning booking emails, PDFs, and
screenshots into typed data with Bedrock's multimodal Converse API

---

Every travel agent app faces the same cold-start problem: the user's
trip lives in confirmation emails, PDF attachments, and screenshots.
Asking people to re-type it kills the product before it starts. For
Travel Autopilot I wanted ingestion to be one gesture: drop the file,
done. Bedrock's Converse API made that almost embarrassingly small.

## One API, three input shapes

Claude on Bedrock accepts documents and images directly in a converse
message, so the "parser" is a content block plus a prompt:

```python
if file_format == "pdf":
    block = {"document": {"format": "pdf", "name": "booking",
                          "source": {"bytes": data}}}
else:  # png / jpeg / webp / gif screenshots
    block = {"image": {"format": file_format, "source": {"bytes": data}}}

response = client.converse(
    modelId=MODEL_ID,
    messages=[{"role": "user", "content": [block, {"text": PROMPT}]}],
    inferenceConfig={"maxTokens": 4096, "temperature": 0.0},
)
```

No OCR pipeline, no PDF text extraction library, no HTML e-mail
untangling for the hard cases. `.eml` files get flattened to text
locally (Python's `email` module) because that's cheaper, but PDFs and
screenshots go to the model as-is.

## The contract: the model proposes, Pydantic disposes

The prompt demands a bare JSON array with a fixed schema — booking type,
provider, confirmation number, ISO 8601 times, locations. The reply is
validated with a Pydantic `TypeAdapter(list[BookingRecord])`, so a
hallucinated field name or a malformed date is a caught exception, not
corrupted trip state. Two defensive touches proved essential: a regex
that tolerates models wrapping output in ```json fences anyway, and
attaching the raw source text to every record for auditability.

## Testability without Bedrock

The Bedrock call sits behind an injectable callable:

```python
def extract_bookings(raw_text, invoke=None):
    call = invoke or _bedrock_invoke
    return _parse_output(call(PROMPT.format(raw_text=raw_text)), raw_text)
```

Tests inject a fake `invoke` and exercise parsing, validation,
markdown-fence tolerance, and duplicate handling — the whole pipeline —
without credentials. The real model call is the only untested line, by
design.

## The product moment

In the app, a "missing accommodation for August 19" alert is on screen.
The user drags the hotel's confirmation email onto the page. The model
reads it, the booking lands in the trip state, the deterministic
consistency checker re-runs — and the alert simply disappears. One
gesture, one Bedrock call, and the itinerary heals itself.

*Travel Autopilot: [repo URL]. Built with Strands Agents SDK, Amazon
Bedrock, and Bedrock AgentCore for the Agents for Humans hackathon.*
