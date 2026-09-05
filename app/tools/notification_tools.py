"""Notification tool: the ONLY way the agent may interrupt the traveler."""

from strands import tool

from app.models.alert import Alert, AlertType

# Alerts sent during this process (used by the demo runner and tests).
sent_alerts: list[Alert] = []


@tool
def notify_user(
    alert_type: str,
    title: str,
    message: str,
    requires_user_action: bool = True,
) -> str:
    """Send a notification to the traveler. Use ONLY when intervention is
    truly required — silence is preferred when nothing needs attention.

    alert_type must be one of: booking_conflict, departure_required,
    transport_problem, free_time, decision_required.
    """
    alert = Alert(
        alert_type=AlertType(alert_type),
        title=title,
        message=message,
        requires_user_action=requires_user_action,
    )
    sent_alerts.append(alert)
    print(f"\n🔔 [{alert.title}] {alert.message}\n")
    return "Notification delivered to the traveler."
