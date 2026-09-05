# Demo Video Script (max 5:00)

Recording setup: switch `.env` to Sonnet
(`BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0`),
`uvicorn app.main:app`, browser at 110% zoom, press "Reset trip" first.
Voiceover over screen capture; no camera needed.

---

## 0:00–0:40 — The problem

*Show: a phone photo of a trip / the itinerary screen.*

> This summer in Switzerland I made the same discovery every traveler
> makes: a trip is a stream of tiny decisions. Which train? When do I
> leave for the airport? What do I do with a free afternoon?
> Chat assistants don't help unless you ask. The problem isn't answering
> questions — it's having to think of the question at all.

## 0:40–1:10 — The idea

*Show: the app, "All quiet" state.*

> Travel Autopilot is an autonomous agent built on the Strands Agents SDK
> and Amazon Bedrock. It holds your entire trip as state, quietly
> monitors it, and speaks only when your attention is actually needed.
> Notice the status: "All quiet". For this agent, silence is a success.

## 1:10–2:20 — Scenario 1: the missing night

*Click "1 Booking conflict".*

> Deterministic checks — plain Python, no AI, no cost — cross-check every
> booking. Here they've caught something subtle: no accommodation for
> August 19.

*Click "Generate today's plan" → blocked message appears.*

> And the agent refuses to plan on top of a broken itinerary.

*Drag the confirmation .eml into "Add bookings".*

> Fixing it is one drag: drop the hotel's confirmation email. A Bedrock
> model reads the unstructured email into a structured booking…

*Alert disappears, "All quiet".*

> …the gap closes, and the agent goes quiet again.

## 2:20–3:20 — Scenario 2: unexpected free time

*Click "2 Unexpected free time". Type into "Tell the agent":
"Finished early — I'm at Gornergrat now, any suggestions?" → Ask Agent.*

> Real trips drift. You finish early, you're somewhere unplanned. Tell
> the agent once: it updates the trip state to match reality, decides it
> needs current local information, searches the web — and proposes
> options that still get you to dinner at seven.

## 3:20–4:00 — Scenario 3: the airport

*Click "3 Airport departure" → alert is already showing.*

> And the flagship moment: nobody asked anything here. The agent worked
> out airport lead time from the flight itself and interrupted exactly
> once, exactly when it mattered: "It is time to leave for the airport."

## 4:00–4:40 — How it works

*Show: architecture diagram.*

> The design rule: LLMs never do arithmetic; Python never guesses.
> Deterministic services compute facts — gaps, overlaps, lead times.
> The Strands agent on Bedrock makes judgments — notify or stay silent,
> search or not — through five tools. Everything below the agent is unit
> tested with zero LLM calls, and the agent deploys to Bedrock AgentCore.

## 4:40–5:00 — Close

> Travel Autopilot is an Everyday Agent in the most literal sense: it
> gives travelers back the headspace their logistics used to consume.
> Interrupt humans only when necessary — and otherwise, stay quiet.

---

### Shot checklist

- [ ] Reset trip before recording
- [ ] Prepare `hotel-confirmation.eml` on the desktop for the drag shot
- [ ] Sonnet model in `.env`; one rehearsal run of each Bedrock action
- [ ] Record at 1920×1080, hide bookmarks bar and notifications
