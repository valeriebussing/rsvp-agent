
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from rsvp_agent.rsvp_logic.guest_record import Attendance


class RSVPUpdate(BaseModel):
    """RSVP changes proposed by the LLM, not yet applied to guest state."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    day_1: Attendance | None = Field(
        default=None,
        description="Proposed attendance for day 1. None means no proposed change.",
    )
    day_2: Attendance | None = Field(
        default=None,
        description="Proposed attendance for day 2. None means no proposed change.",
    )
    day_3: Attendance | None = Field(
        default=None,
        description="Proposed attendance for day 3. None means no proposed change.",
    )
    plus_ones: int | None = Field(
        default=None,
        ge=0,
        description="Proposed number of additional guests. Must be non-negative.",
    )
    food_allergies: str | None = Field(
        default=None,
        description=(
            "Proposed allergy information. None means no proposed change; "
            "use an appropriate string such as 'none' if the guest has no allergies."
        ),
    )
    hotel_needed: Attendance | None = Field(
        default=None,
        description="Whether the guest needs a hotel. None means no proposed change.",
    )


class LLMResponse(BaseModel):
    """Structured result returned by the LLM for one incoming message."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    interpretation: str = Field(
        min_length=1,
        description="A concise interpretation of what the guest communicated.",
    )
    proposed_update: RSVPUpdate = Field(
        description="Proposed RSVP changes for the application to validate.",
    )
    reply_draft: str = Field(
        min_length=1,
        description="A draft reply to the guest in the appropriate language.",
    )