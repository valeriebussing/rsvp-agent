from rsvp_agent.agent.schemas import RSVPUpdate, LLMResponse
from rsvp_agent.rsvp_logic.event_config import EventConfig
from rsvp_agent.rsvp_logic.guest_record import GuestRecord


def calculate_rsvp_status(
    guest: GuestRecord,
    event: EventConfig,
) -> str:
    """Calculate RSVP status from the event requirements and guest answers"""
    if all(guest.attendance.get(day.id, "unknown") == "no" for day in event.days):
        return "declined"

    if any(guest.attendance.get(day.id, "unknown") == "unknown" for day in event.days):
        return "pending"

    field_values = {
        "plus_ones": guest.plus_ones,
        "food_allergies": guest.food_allergies,
        "hotel_needed": guest.hotel_needed,
    }

    for field in event.required_fields:
        if field not in field_values:
            raise ValueError(f"Unsupported required RSVP field: {field}")

        value = field_values[field]
        if value is None or value == "unknown":
            return "pending"

    return "complete"


def apply_rsvp_update(
    guest: GuestRecord,
    update: RSVPUpdate,
    event: EventConfig,
) -> GuestRecord:
    """Validate and apply an LLM-proposed update to a guest record"""
    valid_day_ids = {day.id for day in event.days}
    unknown_day_ids = set(update.attendance) - valid_day_ids

    if unknown_day_ids:
        raise ValueError(f"Unknown event day IDs: {sorted(unknown_day_ids)}")

    # set each day's value as 'unknown' so they're not missing from dict while guest hasn't answered yet
    attendance = {day.id: guest.attendance.get(day.id, "unknown") for day in event.days}
    attendance.update(update.attendance)

    changes = {"attendance": attendance}

    for field in ("plus_ones", "food_allergies"):
        value = getattr(update, field)
        if value is not None:
            changes[field] = value

    updated_guest = guest.model_copy(update=changes)

    # Apply LLM proposed update to a copy only
    updated_guest = updated_guest.model_copy(
        update={"rsvp_status": calculate_rsvp_status(updated_guest, event)}
    )

    return updated_guest


def validate_llm_response(
    response: LLMResponse,
    event: EventConfig,
) -> None:
    """Validate an LLM response before applying its proposed rsvp changes"""

    valid_day_ids = {day.id for day in event.days}
    proposed_day_ids = set(response.proposed_update.attendance)

    unknown_day_ids = proposed_day_ids - valid_day_ids
    if unknown_day_ids:
        raise ValueError(
            f"LLM proposed updates for unknown event days: {sorted(unknown_day_ids)}"
        )

    if response.attendance_clarification_needed and proposed_day_ids:
        raise ValueError(
            "LLM flagged attendance as ambiguous but also proposed attendance updates"
            "Review the proposed updates before applying them"
        )
