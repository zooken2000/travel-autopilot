# Travel Autopilot - Development Context

## Project Goal

Travel Autopilot is an autonomous AI travel agent.

Its purpose is NOT simply to answer travel questions.

It maintains awareness of:

- the user's itinerary
- bookings
- current time
- current location
- upcoming events
- itinerary changes

It quietly monitors the trip and only interrupts the user when action or a decision is required.

Core principle:

> Search and reason autonomously.
> Interrupt humans only when necessary.

---

## Hackathon

Agents for Humans Hackathon

Track: Everyday Agent

Deadline: 2026-09-15 09:00 JST

Required technology:

- Strands Agents SDK
- Amazon Bedrock
- Amazon Bedrock AgentCore deployment is preferred

---

## Problem Statement

Travelers spend significant time making many small decisions during a trip.

Examples:

- What train should I take next?
- Where do I transfer?
- Is my travel pass valid?
- What is today's plan?
- What should I do with unexpected free time?
- When should I leave for the airport?

Traditional travel assistants are reactive. The user must explicitly ask a question.

Travel Autopilot is proactive. It understands the trip context and determines whether intervention is required.

---

## Core Agent Behavior

The agent follows this loop:

1. Understand current trip state.
2. Identify the next relevant event.
3. Determine whether external information is required.
4. Search the web only when needed.
5. Evaluate whether the user needs to act.
6. Stay silent if no action is required.
7. Notify the user only when intervention is useful.

Pseudo code:

```python
trip_state = get_trip_state()
next_event = find_next_event(trip_state)

if needs_external_information(next_event):
    information = search_web()

decision = evaluate(trip_state, next_event, information)

if decision.requires_user_attention:
    notify_user(decision)
else:
    remain_silent()
```

---

## MVP Scope

### 1. Trip Memory

Store: flights, hotels, trains, activities, itinerary changes.

The itinerary must represent the CURRENT plan. Do not preserve outdated plans as active plans. Changes must update trip state.

### 2. Current Situation Awareness

The system receives: current datetime, approximate current location.

For MVP: current location can be inferred from itinerary. Manual override is allowed. Do NOT implement GPS tracking unless required later.

### 3. Autonomous Monitoring

The agent checks:

- What is happening next?
- How much time remains?
- Does the user need to act?
- Is external information required?

If nothing is wrong: DO NOTHING. Silence is a successful agent action.

### 4. Web Search

The agent may search the web for: transportation schedules, delays, attraction opening hours, airport information, activities during unexpected free time.

The agent decides WHEN web search is necessary. Do not search the web unnecessarily. Web search is a tool. It is not the product itself.

### 5. Smart Intervention

Notify the user when:

- departure time is approaching
- transportation changes affect the itinerary
- the user may miss an event
- there is a booking conflict
- unexpected free time exists
- a decision is required

Do not notify when:

- everything is normal
- there is sufficient time
- no action is required

---

## Required Demo Scenarios

### Scenario 1: Booking Conflict

Input: flight and hotel bookings.

The system detects: "⚠️ No accommodation found for August 19."

The agent must prevent itinerary generation until the conflict is resolved.

### Scenario 2: Unexpected Free Time

Current time: 14:00 / Next scheduled event: 19:00 / Current location: Zermatt

The agent recognizes unexpected free time, searches the web for relevant activities, and proposes options based on available time, location, and itinerary constraints.

### Scenario 3: Airport Departure Alert

Flight: 15:55 / Recommended airport arrival: 12:55 / Current time: 12:30

The agent determines that action is required.

Output: "🔔 It is time to leave for the airport."

---

## Architecture Principles

Use LLMs for:

- understanding unstructured booking information
- reasoning about ambiguous situations
- deciding whether web search is needed
- selecting relevant tools

Use deterministic Python logic for:

- datetime calculations
- schedule overlap detection
- booking conflicts
- notification thresholds

Do NOT use LLMs for simple calculations.

---

## Code Quality Rules

- Python 3.11+
- Type hints required
- Pydantic models preferred
- Functions should be small
- Business logic must be testable without LLM calls
- No hardcoded demo behavior in production code
- Demo data must be stored separately

---

## Scope Control

DO NOT implement: real booking, payments, airline ticket modification, hotel reservation modification, OAuth integrations, Gmail API, Outlook API, native mobile application, full GPS tracking.

Future features must not be added unless explicitly requested. Focus on a polished MVP.

---

## Development Priority

P0: Trip models, Trip state, Booking extraction, Consistency checking, Itinerary generation, Monitoring loop, Agent tool integration

P1: Web search, UI, AgentCore deployment

P2: Automatic email ingestion, Maps integration, push notifications

---

## Important

Do not redesign the project architecture unnecessarily.

Prefer simple implementations.

A working demo is more valuable than an ambitious incomplete system.
