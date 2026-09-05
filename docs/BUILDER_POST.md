# builder.aws.com Post Draft (bonus submission)

**Title:** Agents for Humans: Teaching an agent to stay quiet with
Strands Agents and Amazon Bedrock

> Rule note: up to 3 posts count for bonus points (0.2 each, max 0.6).
> Every title must contain "Agents for Humans". Posts 2 and 3 are in
> BUILDER_POST_2.md and BUILDER_POST_3.md.

---

Most agent demos show off what the agent says. Building Travel Autopilot
for the Agents for Humans hackathon, I spent most of my time on the
opposite problem: teaching the agent when to say nothing.

## The problem

A trip is a stream of micro-decisions — which train, when to leave for
the airport, what to do with a surprise free afternoon. Chat assistants
only help when you ask. The real burden is having to think of the
question. So the product goal became: an agent that holds the trip and
interrupts only when attention is genuinely required. Silence is a
successful action.

## Architecture: LLMs never do arithmetic, Python never guesses

The system splits into two layers. Deterministic Python computes facts:
schedule overlaps, accommodation-gap nights, flight lead times,
free-time windows. These are pure functions with unit tests and zero
LLM calls. The Strands agent, running Claude on Amazon Bedrock, consumes
those facts and makes judgments through five tools: get_trip_state,
update_trip_state, check_next_event, search_web, notify_user.

This split paid off three times over. Cost: monitoring passes are free;
Bedrock is invoked only when judgment is needed. Testability: 50+ tests
run in under a second with no AWS access. Trust: the agent cannot
miscalculate a departure time, because it never calculates one.

## What the domain taught the code

Two bugs made the design real. First, my gap detector flagged the last
night of the trip as "no accommodation" — the traveler was asleep on the
overnight flight home. Overnight transport now counts as lodging.
Second, free-time detection proudly announced "25 hours free" — the gap
between an evening and the next morning's train. Free time now only
counts within the same day. Deterministic rules are where domain
knowledge lives; the LLM shouldn't have to rediscover travel common
sense on every call.

## Reading bookings nobody structured

Bedrock's multimodal Converse API turned booking ingestion from a
parsing project into a prompt: users drop an .eml, a PDF, or a
screenshot, and the model returns JSON validated into Pydantic
BookingRecords. The demo's favorite moment: a "missing hotel night"
alert visibly disappearing the second the confirmation email lands.

## Deploying the agent itself

The FastAPI UI runs anywhere, but the agent deploys to Amazon Bedrock
AgentCore Runtime with the AgentCore CLI — the same entrypoint serves
autonomous monitoring cycles and traveler requests ("Finished early,
I'm at Gornergrat — suggestions?").

## Takeaway

If you're building an everyday agent, decide early what your agent will
refuse to do. Mine refuses to do arithmetic, refuses to plan on top of a
broken itinerary, and above all refuses to talk when there's nothing to
say. Those refusals, more than any prompt, are what make it feel less
like a chatbot and more like an autopilot.

*Travel Autopilot: [repo URL]. Built with Strands Agents SDK, Amazon
Bedrock, and Bedrock AgentCore.*
