from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Attendance = Literal["yes", "no", "unknown"]
RSVPStatus = Literal["pending", "complete", "declined"]


class GuestRecord(BaseModel):
    """current rsvp info stored for one guest"""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str
    phone: str
    language: str = "en"

    # Keys must match exact day IDs defined in event.json
    attendance: dict[str, Attendance] = Field(default_factory=dict)

    plus_ones: int | None = Field(default=None, ge=0)
    # None means not answered, "none" means no allergies
    food_allergies: str | None = None
    hotel_needed: Attendance = "unknown"

    rsvp_status: RSVPStatus = "pending"
