from datetime import datetime
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict

from rsvp_agent.rsvp_logic.guest_record import GuestRecord

MessageRole = Literal["guest", "assistant"]


class ConversationMessage(BaseModel):
    """One message stored in the conversation history"""

    model_config = ConfigDict(str_strip_whitespace=True)

    timestamp: datetime
    phone: str
    role: MessageRole
    content: str


class GuestRepository(Protocol):
    """Storage operations for current guest rsvp state"""

    def get_by_phone(self, phone: str) -> GuestRecord | None:
        """Return guest that matches phone number, or else None"""
        ...

    def update(self, guest: GuestRecord) -> None:
        """Persist changes to an existing guest record"""
        ...


class MessageRepository(Protocol):
    """Storage operations for convo mssg history"""

    def get_recent(
        self,
        phone: str,
        limit: int = 3,
    ) -> list[ConversationMessage]:
        """Return up to [limit] mssg, ordered oldest to newest"""
        ...

    def append(
        self,
        phone: str,
        role: MessageRole,
        content: str,
    ) -> None:
        """Append mssg to convo history"""
        ...
