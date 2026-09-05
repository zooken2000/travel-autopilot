# Devpost Submission Draft

**Project name:** Travel Autopilot
**Track:** Everyday Agents
**Elevator:** An autonomous AI agent, built with the **Strands Agents SDK**
on **Amazon Bedrock**, that quietly manages your trip and intervenes only
when you need to decide.

---

## Inspiration

On a trip through Switzerland, I counted the questions a traveler
answers in a single day: which train, which transfer, when to leave,
what to do with a free hour. Dozens of micro-decisions, all day, every
day. Chat assistants only help if you think to ask — so the cognitive load
never goes away. I wanted an agent that carries the trip so the traveler
doesn't have to. That turned out to be close to how this hackathon's own
Everyday Agents track describes its goal — an agent that runs quietly
and pings you only when there's a real decision to make. I found that
phrasing after the core design was already built, which felt like a good
sign I was solving the right problem.

## What it does

Travel Autopilot holds the whole trip — flights, hotels, trains,
activities, current time and location — as a single TripState for anyone
juggling a multi-leg personal trip, and runs an autonomous loop over it:
observe → compute facts → judge → act or stay silent. It detects booking
conflicts ("No accommodation found for
August 19") and blocks itinerary planning until they're resolved; it
ingests booking confirmations by drag-and-drop (.eml, PDF, or a
screenshot — the model reads them directly); it recognizes unexpected
free time and, when asked, searches the web for suggestions that fit the
location, the time window, and the next fixed commitment; and it
computes flight lead times and interrupts exactly once, when it's time
to leave for the airport. When nothing needs attention it does nothing:
silence is a successful agent action.

## How we built it

The agent is built on the **Strands Agents SDK** with **Amazon Bedrock**
(Claude) as the model, holding five tools: get_trip_state,
update_trip_state, check_next_event, search_web, notify_user. The core
design rule: **LLMs never do arithmetic; Python never guesses.**
Deterministic, unit-tested Python computes every fact (schedule
overlaps, accommodation gaps, departure lead times, free-time windows);
the LLM makes judgments — whether to interrupt, whether fresh external
information is needed, how to phrase advice. Bedrock's multimodal
Converse API reads PDFs and screenshots of bookings into validated
Pydantic records. A FastAPI + single-page UI shows the itinerary
timeline and the agent's notifications. The agent deploys to **Amazon
Bedrock AgentCore Runtime**.

## Challenges we ran into

Getting an agent to *not* act is harder than getting it to act. We
moved every threshold decision into deterministic code and instructed
the agent that silence is preferred — then verified with tests that a
healthy trip produces zero alerts. Subtle domain logic also bit us:
overnight flights looked like missing hotel nights, and 25-hour
overnight "free time" looked like an opportunity, until the rules
learned what real travel looks like.

## Accomplishments we're proud of

A demo where every scenario runs through real business logic — nothing
is hardcoded; 50+ unit tests that run without a single LLM call; and a
booking-ingestion flow where dropping one email visibly heals a broken
itinerary.

## What we learned

The value of an "agent" isn't the conversation — it's the judgment
about when a conversation is even necessary. Splitting fact-computation
(deterministic) from judgment (LLM) made the system cheaper, testable,
and more trustworthy.

## What's next

Continuous background monitoring with push notifications, phone GPS for
automatic situation updates, email forwarding for zero-touch booking
ingestion, and multi-trip support.

---

### Testing instructions for judges (paste into Devpost "testing" field)

> Everything except the LLM calls runs with zero AWS setup: clone the
> repo, `pip install -e ".[dev]"`, then `pytest` (53 tests, no LLM
> calls) and `python scripts/run_demo.py` (all three scenarios through
> the real business logic). `uvicorn app.main:app` starts the web UI at
> http://127.0.0.1:8000 — every button except "Ask Agent",
> "Extract & add", and "Generate today's plan" is deterministic and
> free. To exercise the agent itself, set AWS credentials with Bedrock
> model access in `.env` (see `.env.example`); the agent is also
> deployed on Amazon Bedrock AgentCore Runtime (ARN in this
> description). The demo video shows every paid path end-to-end.

### Submission checklist

- [ ] Public repo (MIT license visible in the repo About / top level)
- [ ] README + setup instructions + judge quick-start section
- [ ] Architecture diagram (docs/images/architecture.png) uploaded
- [ ] Demo video ≤ 5 min, PUBLIC on YouTube/Vimeo, English (or English
      subtitles) — shows the working project end-to-end + problem /
      audience / why it matters
- [ ] AWS Builder ID linked
- [ ] Testing instructions filled (block above) + AgentCore runtime ARN
- [ ] Everything stays public & the AgentCore runtime stays up through
      the JUDGING period (ends Oct 8, 2026) — tear down only after
- [ ] $50 AWS credits requested (deadline Sep 11, 12:00 PT — form on
      the hackathon Resources page)
- [ ] (Bonus, up to +0.6) up to THREE builder.aws.com posts, each with
      "Agents for Humans" in the title: docs/BUILDER_POST.md,
      BUILDER_POST_2.md, BUILDER_POST_3.md
- [ ] Disclose standard tooling used (agentcore CLI scaffold for the
      CDK app; AI coding assistants — explicitly permitted by the rules)
