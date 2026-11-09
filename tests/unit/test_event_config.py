import pytest
from pydantic import ValidationError

from rsvp_agent.rsvp_logic.event_config import EventConfig, EventDay


def test_event_day_accepts_valid_id_and_name():
    day = EventDay(id="fri", name="Friday", day_number=1)

    assert day.id == "fri"
    assert day.name == "Friday"
    assert day.day_number == 1


@pytest.mark.parametrize("field", ["id", "name"])
def test_event_day_rejects_empty_id_or_name(field):
    data = {"id": "fri", "name": "Friday", "day_number": 1}
    data[field] = ""

    with pytest.raises(ValidationError):
        EventDay(**data)


@pytest.mark.parametrize("number_of_days", [1, 2])
def test_event_config_accepts_one_or_multiple_days(number_of_days):
    days = [
        EventDay(id="fri", name="Friday", day_number=1),
        EventDay(id="sat", name="Saturday", day_number=2),
    ]

    event = EventConfig(
        event_id="wedding-2027",
        name="Val's Wedding",
        days=days[:number_of_days],
    )

    assert len(event.days) == number_of_days


def test_event_config_rejects_empty_days_list():
    with pytest.raises(ValidationError):
        EventConfig(
            event_id="wedding-2027",
            name="Val's Wedding",
            days=[],
        )


def test_event_config_applies_default_required_fields():
    event = EventConfig(
        event_id="wedding-2027",
        name="Val's Wedding",
        days=[EventDay(id="fri", name="Friday", day_number=1)],
    )

    assert event.required_fields == {
        "plus_ones",
        "food_allergies",
        "hotel_needed",
    }
