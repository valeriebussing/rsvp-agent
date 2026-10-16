import pytest
from pydantic import ValidationError

from rsvp_agent.rsvp_logic.guest_record import GuestRecord


def test_guest_record_accepts_required_fields():
    guest = GuestRecord(
        name="Valerie Andrea",
        phone="+31612345678",
    )

    assert guest.name == "Valerie Andrea"
    assert guest.phone == "+31612345678"


def test_guest_record_applies_defaults():
    guest = GuestRecord(
        name="Valerie Andrea",
        phone="+31612345678",
    )

    assert guest.language == "en"
    assert guest.day_1 == "unknown"
    assert guest.day_2 == "unknown"
    assert guest.day_3 == "unknown"
    assert guest.plus_ones == 0
    assert guest.food_allergies == "unknown"
    assert guest.hotel_needed == "unknown"
    assert guest.rsvp_status == "incomplete"


def test_guest_record_accepts_valid_rsvp_data():
    guest = GuestRecord(
        name="Valerie Andrea",
        phone="+31612345678",
        language="nl",
        day_1="yes",
        day_2="no",
        day_3="unknown",
        plus_ones=2,
        food_allergies="Gluten",
        hotel_needed="yes",
        rsvp_status="complete",
    )

    assert guest.language == "nl"
    assert guest.day_1 == "yes"
    assert guest.day_2 == "no"
    assert guest.plus_ones == 2
    assert guest.food_allergies == "Gluten"
    assert guest.hotel_needed == "yes"
    assert guest.rsvp_status == "complete"


def test_guest_record_strips_surrounding_whitespace():
    guest = GuestRecord(
        name="  Valerie Andrea  ",
        phone=" +31612345678 ",
        language=" en ",
    )

    assert guest.name == "Valerie Andrea"
    assert guest.phone == "+31612345678"
    assert guest.language == "en"


@pytest.mark.parametrize("field", ["name", "phone"])
def test_guest_record_requires_name_and_phone(field):
    data = {"name": "Valerie Andrea", "phone": "+31612345678"}
    del data[field]

    with pytest.raises(ValidationError):
        GuestRecord(**data)


@pytest.mark.parametrize("field", ["day_1", "day_2", "day_3", "hotel_needed"])
@pytest.mark.parametrize("invalid_value", ["maybe", "yes please", ""])
def test_guest_record_rejects_invalid_attendance(field, invalid_value):
    with pytest.raises(ValidationError):
        GuestRecord(
            name="Valerie Andrea",
            phone="+31612345678",
            **{field: invalid_value},
        )


@pytest.mark.parametrize("invalid_status", ["pending", "finished", "yes"])
def test_guest_record_rejects_invalid_rsvp_status(invalid_status):
    with pytest.raises(ValidationError):
        GuestRecord(
            name="Valerie Andrea",
            phone="+31612345678",
            rsvp_status=invalid_status,
        )


def test_guest_record_rejects_negative_plus_ones():
    with pytest.raises(ValidationError):
        GuestRecord(
            name="Valerie Andrea",
            phone="+31612345678",
            plus_ones=-1,
        )
