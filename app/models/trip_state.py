"""TripState: the single source of truth the agent reads on every decision."""

from datetime import datetime

from pydantic import BaseModel

from app.models.booking import BookingRecord


class TripState(BaseModel):
    trip_id: str

    current_time: datetime

    current_location: str | None = None

    bookings: list[BookingRecord]

    updated_at: datetime
