from pydantic import BaseModel, ConfigDict, Field

from rsvp_agent.rsvp_logic.guest_record import Attendance


class RSVPUpdate(BaseModel):
    """RSVP changes proposed by the LLM, not yet applied to guest state"""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    attendance: dict[str, Attendance] = Field(
        default_factory=dict,
        description=(
            "Attendance changes keyed by configured event-day ID "
            "Include only days the guest has provided an answer for"
        ),
    )
    plus_ones: int | None = Field(default=None, ge=0)
    food_allergies: str | None = Field(
        default=None,
        description=(
            "Use 'none' when the guest explicitly reports no allergies"
            "None means no proposed change"
        ),
    )
    hotel_needed: Attendance | None = Field(default=None)


class LLMResponse(BaseModel):
    """Structured result returned by the LLM per incoming text"""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    interpretation: str = Field(min_length=1)
    proposed_update: RSVPUpdate
    attendance_clarification_needed: bool = Field(
        description=(
            "True if the guest's attendance is ambiguous for any event day and the assistant needs to ask for clarification"
        )
    )
    reply_draft: str = Field(min_length=1)
