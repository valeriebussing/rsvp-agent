import os
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from collections.abc import Iterator

from rsvp_agent.integrations.google_sheets import GoogleSheetsRepository
from rsvp_agent.persistence.repositories import (
    ConversationMessage,
    GuestRepository,
    MessageRepository,
)
from rsvp_agent.rsvp_logic.guest_record import GuestRecord


load_dotenv()

pytestmark = pytest.mark.integration


@pytest.fixture
def repository() -> GoogleSheetsRepository:
    if not os.getenv("GOOGLE_SHEET_ID"):
        pytest.skip("GOOGLE_SHEET_ID is not configured")

    if not os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE"):
        pytest.skip("Google credentials are not configured")

    return GoogleSheetsRepository()


@pytest.fixture
def test_guest(
    repository: GoogleSheetsRepository,
) -> Iterator[GuestRecord]:
    # Unique synthetic phone identifier for each test run.
    # Never use this value to send real WhatsApp messages.
    phone = f"test-{uuid4().hex}"

    guest = GuestRecord(
        name="Amelia Bennett",
        phone=phone,
        language="en",
    )

    repository.create(guest)

    try:
        yield guest
    finally:
        delete_test_rows(repository, "MessageHistory", phone)
        delete_test_rows(repository, "Guests", phone)


def test_repository_implements_protocols(
    repository: GoogleSheetsRepository,
) -> None:
    assert isinstance(repository, GuestRepository)
    assert isinstance(repository, MessageRepository)


def test_read_guest(
    repository: GoogleSheetsRepository,
    test_guest: GuestRecord,
) -> None:
    guest = repository.get_by_phone(test_guest.phone)

    assert guest is not None
    assert guest.name == "Amelia Bennett"
    assert guest.attendance == {}
    assert guest.rsvp_status == "pending"


def test_update_guest(
    repository: GoogleSheetsRepository,
    test_guest: GuestRecord,
) -> None:
    updated_guest = test_guest.model_copy(
        update={
            "attendance": {"fri": "yes", "sat": "unknown"},
            "plus_ones": 1,
            "food_allergies": "none",
        }
    )

    repository.update(updated_guest)
    saved_guest = repository.get_by_phone(test_guest.phone)

    assert saved_guest is not None
    assert saved_guest.attendance == {
        "fri": "yes",
        "sat": "unknown",
    }
    assert saved_guest.plus_ones == 1
    assert saved_guest.food_allergies == "none"


def test_unknown_guest_returns_none(
    repository: GoogleSheetsRepository,
) -> None:
    assert repository.get_by_phone(f"missing-{uuid4().hex}") is None


def test_append_and_read_messages(
    repository: GoogleSheetsRepository,
    test_guest: GuestRecord,
) -> None:
    repository.append(
        phone=test_guest.phone,
        role="guest",
        content="I'll attend Friday!",
    )

    repository.append(
        phone=test_guest.phone,
        role="assistant",
        content="Great! What about Saturday?",
    )

    messages = repository.get_recent(
        phone=test_guest.phone,
        limit=3,
    )

    assert len(messages) == 2
    assert all(isinstance(message, ConversationMessage) for message in messages)

    assert messages[0].role == "guest"
    assert messages[0].content == "I'll attend Friday!"

    assert messages[1].role == "assistant"
    assert messages[1].content == "Great! What about Saturday?"

    assert messages[0].timestamp <= messages[1].timestamp


def test_recent_messages_respects_limit(
    repository: GoogleSheetsRepository,
    test_guest: GuestRecord,
) -> None:
    for index in range(4):
        repository.append(
            phone=test_guest.phone,
            role="guest",
            content=f"Message {index}",
        )

    messages = repository.get_recent(
        phone=test_guest.phone,
        limit=2,
    )

    assert [message.content for message in messages] == [
        "Message 2",
        "Message 3",
    ]


def delete_test_rows(
    repository: GoogleSheetsRepository,
    tab: str,
    phone: str,
) -> None:
    """Delete rows belonging to one test guest"""

    rows = repository._read_rows(tab)

    phone_column = 0 if tab == "Guests" else 1

    matching_row_numbers = [
        row_number
        for row_number, row in enumerate(rows[1:], start=2)
        if len(row) > phone_column and row[phone_column] == phone
    ]

    if not matching_row_numbers:
        return

    # Fetch spreadsheet metadata to find the tab's numeric sheet ID
    spreadsheet = (
        repository.service.spreadsheets()
        .get(spreadsheetId=repository.spreadsheet_id)
        .execute()
    )

    sheet_id = next(
        sheet["properties"]["sheetId"]
        for sheet in spreadsheet["sheets"]
        if sheet["properties"]["title"] == tab
    )

    # Delete bottom-up so earlier row numbers don't shift
    requests = [
        {
            "deleteDimension": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": row_number - 1,
                    "endIndex": row_number,
                }
            }
        }
        for row_number in reversed(matching_row_numbers)
    ]

    repository.service.spreadsheets().batchUpdate(
        spreadsheetId=repository.spreadsheet_id,
        body={"requests": requests},
    ).execute()
