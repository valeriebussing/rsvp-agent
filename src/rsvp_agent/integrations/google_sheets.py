import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from uuid import uuid4

from rsvp_agent.rsvp_logic.guest_record import GuestRecord
from rsvp_agent.persistence.repositories import (
    ConversationMessage,
    MessageRole,
)


GUEST_COLUMNS = [
    "phone",
    "name",
    "language",
    "attendance",
    "plus_ones",
    "food_allergies",
    "hotel_needed",
    "rsvp_status",
]

MESSAGE_COLUMNS = [
    "message_sid",
    "phone",
    "role",
    "content",
    "timestamp",
]


class GoogleSheetsRepository:
    """Read and write rsvp data in a Google sheet"""

    def __init__(self) -> None:
        load_dotenv()

        spreadsheet_id = os.environ["GOOGLE_SHEET_ID"]
        credentials_path = Path(os.environ["GOOGLE_SERVICE_ACCOUNT_FILE"])

        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path),
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )

        self.spreadsheet_id = spreadsheet_id
        self.service = build(
            "sheets",
            "v4",
            credentials=credentials,
            cache_discovery=False,
        )
        self.sheets = self.service.spreadsheets().values()

    def _read_rows(self, tab: str) -> list[list[str]]:
        result = self.sheets.get(
            spreadsheetId=self.spreadsheet_id,
            range=f"'{tab}'!A:Z",
        ).execute()

        return result.get("values", [])

    def _write_row(self, tab: str, row_number: int, values: list[str]) -> None:
        self.sheets.update(
            spreadsheetId=self.spreadsheet_id,
            range=f"'{tab}'!A{row_number}",
            valueInputOption="RAW",
            body={"values": [values]},
        ).execute()

    def _append_row(self, tab: str, values: list[str]) -> None:
        self.sheets.append(
            spreadsheetId=self.spreadsheet_id,
            range=f"'{tab}'!A:Z",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [values]},
        ).execute()

    def get_by_phone(self, phone: str) -> GuestRecord | None:
        rows = self._read_rows("Guests")

        for row in rows[1:]:
            cells = dict(zip(GUEST_COLUMNS, row))
            if cells.get("phone") == phone:
                return self._deserialize_guest(cells)

        return None

    def update(self, guest: GuestRecord) -> None:
        rows = self._read_rows("Guests")
        matching_rows = [
            row_number
            for row_number, row in enumerate(rows[1:], start=2)
            if row and row[0] == guest.phone
        ]

        if len(matching_rows) > 1:
            raise ValueError(f"Duplicate guest phone number: {guest.phone}")

        values = self._serialize_guest(guest)

        if matching_rows:
            self._write_row("Guests", matching_rows[0], values)
        else:
            raise ValueError(f"Guest phone number does not exist: {guest.phone}")

    def create(self, guest: GuestRecord) -> None:
        rows = self._read_rows("Guests")
        values = self._serialize_guest(guest)

        if any(row and row[0] == guest.phone for row in rows[1:]):
            raise ValueError(f"Duplicate guest phone number: {guest.phone}")

        self._append_row("Guests", values)

    def get_recent(
        self,
        phone: str,
        limit: int = 3,
    ) -> list[ConversationMessage]:
        rows = self._read_rows("MessageHistory")
        messages: list[ConversationMessage] = []

        for row in rows[1:]:
            cells = dict(zip(MESSAGE_COLUMNS, row))

            if cells.get("phone") == phone:
                messages.append(ConversationMessage.model_validate(cells))

        return messages[-limit:] if limit > 0 else []

    def append(
        self,
        phone: str,
        role: MessageRole,
        content: str,
        message_sid: str | None = None,
    ) -> None:
        if role not in {"guest", "assistant"}:
            raise ValueError("role must be guest or assistant")

        # Use the Twilio SID when available; otherwise generate a local ID
        message_id = message_sid or f"local-{uuid4().hex}"

        # Avoid saving the same message twice
        rows = self._read_rows("MessageHistory")
        if any(row and row[0] == message_id for row in rows[1:]):
            return

        timestamp = datetime.now(timezone.utc).isoformat()

        self._append_row(
            "MessageHistory",
            [message_id, phone, role, content, timestamp],
        )

    @staticmethod
    def _serialize_guest(guest: GuestRecord) -> list[str]:
        return [
            guest.phone,
            guest.name,
            guest.language,
            json.dumps(guest.attendance),
            "" if guest.plus_ones is None else str(guest.plus_ones),
            guest.food_allergies or "",
            guest.hotel_needed,
            guest.rsvp_status,
        ]

    @staticmethod
    def _deserialize_guest(cells: dict[str, str]) -> GuestRecord:
        attendance_text = cells.get("attendance", "").strip()

        return GuestRecord(
            phone=cells["phone"],
            name=cells["name"],
            language=cells.get("language") or "en",
            attendance=(json.loads(attendance_text) if attendance_text else {}),
            plus_ones=(int(cells["plus_ones"]) if cells.get("plus_ones") else None),
            food_allergies=cells.get("food_allergies") or None,
            hotel_needed=cells.get("hotel_needed") or "unknown",
            rsvp_status=cells.get("rsvp_status") or "pending",
        )
