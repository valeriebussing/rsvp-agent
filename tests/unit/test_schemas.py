import pytest
from pydantic import ValidationError

from rsvp_agent.agent.schemas import LLMResponse, RSVPUpdate


def test_rsvp_update_defaults_to_no_proposed_changes():
    update = RSVPUpdate()

    assert update.attendance == {}
    assert update.plus_ones is None
    assert update.food_allergies is None
    assert update.hotel_needed is None


def test_rsvp_update_accepts_partial_changes():
    update = RSVPUpdate(
        attendance={"fri": "yes"},
        food_allergies="Gluten",
    )

    assert update.attendance == {"fri": "yes"}
    assert update.food_allergies == "Gluten"
    assert update.plus_ones is None


def test_rsvp_update_accepts_explicit_no_allergies():
    update = RSVPUpdate(food_allergies="none")

    assert update.food_allergies == "none"


@pytest.mark.parametrize("field", ["attendance", "hotel_needed"])
def test_rsvp_update_rejects_invalid_attendance(field):
    with pytest.raises(ValidationError):
        RSVPUpdate(**{field: "maybe"})


def test_rsvp_update_rejects_negative_plus_ones():
    with pytest.raises(ValidationError):
        RSVPUpdate(plus_ones=-1)


def test_rsvp_update_rejects_unexpected_fields():
    with pytest.raises(ValidationError):
        RSVPUpdate(attendance={"fri": "yes"}, unexpected_field="value")


def test_llm_response_accepts_valid_output():
    response = LLMResponse(
        interpretation="The guest confirms attendance on day one",
        proposed_update=RSVPUpdate(attendance={"fri": "yes"}),
        attendance_clarification_needed=False,
        reply_draft="thanks for confirming diva xx",
    )

    assert response.interpretation == ("The guest confirms attendance on day one")
    assert response.proposed_update.attendance == {"fri": "yes"}
    assert response.reply_draft == "thanks for confirming diva xx"


def test_llm_response_accepts_no_proposed_changes():
    response = LLMResponse(
        interpretation="The guest asks about the venue",
        proposed_update=RSVPUpdate(),
        attendance_clarification_needed=False,
        reply_draft="pls read the invitation again hon",
    )

    assert response.proposed_update.attendance == {}
    assert response.reply_draft


@pytest.mark.parametrize(
    "field",
    ["interpretation", "reply_draft"],
)
def test_llm_response_rejects_empty_required_text(field):
    data = {
        "interpretation": "The guest confirms attendance on both days",
        "proposed_update": RSVPUpdate(),
        "attendance_clarification_needed": False,
        "reply_draft": "thanks for confirming diva xx",
    }
    data[field] = "   "

    with pytest.raises(ValidationError):
        LLMResponse(**data)


def test_llm_response_needs_all_required_fields():
    with pytest.raises(ValidationError):
        LLMResponse(
            interpretation="The guest confirms attendance on both days",
            proposed_update=RSVPUpdate(attendance={"fri": "yes", "sat": "yes"}),
            attendance_clarification_needed=False,
            # missing reply_draft raises an error
        )


def test_llm_response_rejects_unexpected_fields():
    with pytest.raises(ValidationError):
        LLMResponse(
            interpretation="The guest confirms attendance on both days",
            proposed_update=RSVPUpdate(attendance={"fri": "yes", "sat": "yes"}),
            attendance_clarification_needed=False,
            reply_draft="thanks for confirming diva xx",
            unexpected_field="value",
        )


def test_llm_response_accepts_attendance_clarification():
    response = LLMResponse(
        interpretation="Guest confirms attendance but days are unclear",
        proposed_update=RSVPUpdate(),
        attendance_clarification_needed=True,
        reply_draft="ok but will you attend both Friday and Saturday tho",
    )

    assert response.attendance_clarification_needed is True


def test_llm_response_doesnt_need_clarification_when_attendance_is_clear():
    response = LLMResponse(
        interpretation="Guest confirms attendance on both days",
        proposed_update=RSVPUpdate(attendance={"fri": "yes", "sat": "yes"}),
        attendance_clarification_needed=False,
        reply_draft="cool cool see you both days!!",
    )

    assert response.attendance_clarification_needed is False
