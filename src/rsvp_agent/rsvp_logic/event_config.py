from pydantic import BaseModel, ConfigDict, Field


class EventDay(BaseModel):
    """A single day/session of an event"""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1, description="Stable identifier e.g. fri")
    name: str = Field(min_length=1, description="Human readable name e.g. Friday")
    day_number: int = Field(ge=1)


class EventConfig(BaseModel):
    """Config describing an event and its rsvp reqs"""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    days: list[EventDay] = Field(min_length=1)

    # Must know a guest's +1s and allergies for their rsvp to be complete
    required_fields: set[str] = Field(
        default_factory=lambda: {"plus_ones", "food_allergies", "hotel_needed"}
    )
