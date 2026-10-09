from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Attendance = Literal["yes", "no", "unknown"]
RSVPStatus = Literal["incomplete", "complete", "declined"]


class GuestRecord(BaseModel):
    """The current RSVP information stored for one guest."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    phone: str
    language: str = "en"

    day_1: Attendance = "unknown"
    day_2: Attendance = "unknown"
    day_3: Attendance = "unknown"

    plus_ones: int = Field(default=0, ge=0)
    food_allergies: str = "unknown"
    hotel_needed: Attendance = "unknown"

    rsvp_status: RSVPStatus = "incomplete"