"""Alert models: the only channel through which the agent interrupts the user."""

from enum import Enum

from pydantic import BaseModel


class AlertType(str, Enum):
    BOOKING_CONFLICT = "booking_conflict"
    DEPARTURE_REQUIRED = "departure_required"
    TRANSPORT_PROBLEM = "transport_problem"
    FREE_TIME = "free_time"
    DECISION_REQUIRED = "decision_required"


class Alert(BaseModel):
    alert_type: AlertType

    title: str

    message: str

    requires_user_action: bool = True
