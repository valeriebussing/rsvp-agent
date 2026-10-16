import pytest
from pydantic import ValidationError

from rsvp_agent.agent.schemas import LLMResponse, RSVPUpdate


def test_rsvp_update_defaults_to_no_proposed_changes():
    update = RSVPUpdate()

    assert update.day_1 is None
    assert update.day_2 is None
    assert update.day_3 is None
    assert update.plus_ones is None
    assert update.food_allergies is None
    assert update.hotel_needed is None


def test_rsvp_update_accepts_partial_changes():
    update = RSVPUpdate(
        day_1="yes",
        food_allergies="Gluten",
    )

    assert update.day_1 == "yes"
    assert update.food_allergies == "Gluten"
    assert update.day_2 is None
    assert update.plus_ones is None


def test_rsvp_update_accepts_explicit_no_allergies():
    update = RSVPUpdate(food_allergies="none")

    assert update.food_allergies == "none"


@pytest.mark.parametrize("field", ["day_1", "day_2", "day_3", "hotel_needed"])
def test_rsvp_update_rejects_invalid_attendance(field):
    with pytest.raises(ValidationError):
        RSVPUpdate(**{field: "maybe"})


def test_rsvp_update_rejects_negative_plus_ones():
    with pytest.raises(ValidationError):
        RSVPUpdate(plus_ones=-1)


def test_rsvp_update_rejects_unexpected_fields():
    with pytest.raises(ValidationError):
        RSVPUpdate(unexpected_field="value")


def test_llm_response_accepts_valid_output():
    response = LLMResponse(
        interpretation="The guest confirms attendance on day one.",
        proposed_update=RSVPUpdate(day_1="yes"),
        reply_draft="Thanks for confirming!",
    )

    assert response.interpretation == ("The guest confirms attendance on day one.")
    assert response.proposed_update.day_1 == "yes"
    assert response.reply_draft == "Thanks for confirming!"


def test_llm_response_accepts_no_proposed_changes():
    response = LLMResponse(
        interpretation="The guest asks about the venue.",
        proposed_update=RSVPUpdate(),
        reply_draft="The venue details are available in your invitation.",
    )

    assert response.proposed_update.day_1 is None
    assert response.reply_draft


@pytest.mark.parametrize(
    "field",
    ["interpretation", "reply_draft"],
)
def test_llm_response_rejects_empty_required_text(field):
    data = {
        "interpretation": "The guest confirms attendance.",
        "proposed_update": RSVPUpdate(),
        "reply_draft": "Thanks for your message!",
    }
    data[field] = "   "

    with pytest.raises(ValidationError):
        LLMResponse(**data)


def test_llm_response_requires_all_top_level_fields():
    with pytest.raises(ValidationError):
        LLMResponse(
            interpretation="The guest confirms attendance.",
            proposed_update=RSVPUpdate(day_1="yes"),
        )


def test_llm_response_rejects_unexpected_fields():
    with pytest.raises(ValidationError):
        LLMResponse(
            interpretation="The guest confirms attendance.",
            proposed_update=RSVPUpdate(day_1="yes"),
            reply_draft="Thanks!",
            unexpected_field="value",
        )
