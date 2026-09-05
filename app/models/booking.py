"""Booking models for Travel Autopilot."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class BookingType(str, Enum):
    FLIGHT = "flight"
    HOTEL = "hotel"
    TRAIN = "train"
    ACTIVITY = "activity"
    OTHER = "other"


class BookingRecord(BaseModel):
    booking_type: BookingType

    provider_name: str

    confirmation_number: str | None = None

    start_time: datetime
    end_time: datetime

    start_location: str
    end_location: str

    notes: str | None = None

    raw_source_text: str | None = None
