import pytest


from rsvp_agent.agent.schemas import RSVPUpdate, LLMResponse
from rsvp_agent.rsvp_logic.event_config import EventConfig, EventDay
from rsvp_agent.rsvp_logic.guest_record import GuestRecord
from rsvp_agent.rsvp_logic.rules import (
    apply_rsvp_update,
    calculate_rsvp_status,
    validate_llm_response,
)


def make_event(*days: tuple[str, str]) -> EventConfig:
    """Create an event with the specified (ID, name) pairs"""
    return EventConfig(
        event_id="test-event",
        name="Test Event",
        days=[
            EventDay(id=day_id, name=name, day_number=i)
            for i, (day_id, name) in enumerate(days, start=1)
        ],
    )


def make_guest(**overrides) -> GuestRecord:
    """Create a guest with valid, complete rsvp details by default"""
    data = {
        "name": "Valerie Andrea",
        "phone": "+31612345678",
        "attendance": {},
        "plus_ones": 0,
        "food_allergies": "none",
        "hotel_needed": "no",
    }
    data.update(overrides)
    return GuestRecord(**data)


def test_one_day_event_can_become_complete():
    event = make_event(("sat", "Saturday"))
    guest = make_guest()

    updated = apply_rsvp_update(
        guest,
        RSVPUpdate(attendance={"sat": "yes"}),
        event,
    )

    assert updated.attendance == {"sat": "yes"}
    assert updated.rsvp_status == "complete"


def test_two_day_event_stays_pending_until_both_days_are_answered():
    event = make_event(("fri", "Friday"), ("sat", "Saturday"))
    guest = make_guest()

    first_update = apply_rsvp_update(
        guest,
        RSVPUpdate(attendance={"fri": "yes"}),
        event,
    )

    assert first_update.rsvp_status == "pending"
    assert first_update.attendance == {"fri": "yes", "sat": "unknown"}

    second_update = apply_rsvp_update(
        first_update, RSVPUpdate(attendance={"sat": "no"}), event
    )

    assert second_update.rsvp_status == "complete"
    assert second_update.attendance == {"fri": "yes", "sat": "no"}


def test_non_event_day_is_not_required():
    event = make_event(("sat", "Saturday"))
    guest = make_guest(attendance={"sat": "yes"})

    assert calculate_rsvp_status(guest, event) == "complete"
    assert "sun" not in guest.attendance


def test_missing_required_information_keeps_rsvp_pending():
    event = make_event(("sat", "Saturday"))
    guest = make_guest(
        attendance={"sat": "yes"},
        food_allergies=None,
    )

    assert calculate_rsvp_status(guest, event) == "pending"


def test_saying_no_to_every_event_day_means_declined():
    event = make_event(("fri", "Friday"), ("sat", "Saturday"))
    guest = make_guest(
        attendance={"fri": "no", "sat": "no"},
    )

    assert calculate_rsvp_status(guest, event) == "declined"


def test_update_with_unknown_day_id_is_rejected():
    event = make_event(("fri", "Friday"))
    guest = make_guest()

    with pytest.raises(ValueError, match="Unknown event day IDs"):
        apply_rsvp_update(guest, RSVPUpdate(attendance={"sun": "yes"}), event)


def test_ambiguous_interpretation_does_not_confirm_all_event_days():
    event = make_event(("fri", "Friday"), ("sat", "Saturday"))

    llm_response = LLMResponse(
        interpretation="Guest confirms attendance, but which days are unclear",
        proposed_update=RSVPUpdate(attendance={"fri": "yes", "sat": "yes"}),
        attendance_clarification_needed=True,
        reply_draft="thanks for confirming diva xx",
    )

    with pytest.raises(ValueError, match="ambiguous"):
        validate_llm_response(llm_response, event)
