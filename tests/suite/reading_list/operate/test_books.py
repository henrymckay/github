import datetime
from typing import TYPE_CHECKING

import pytest

from reading_list.code import error, operate, transform

if TYPE_CHECKING:
    from pytest_.given import MakeDraft, MemoryStore


def test_when_add_book_then_stored_settled(
    memory_store: MemoryStore, make_draft: MakeDraft, today: datetime.date
) -> None:
    added = operate.add_book(
        make_draft(pages_read=300), store=memory_store, today=today
    )
    assert (added.status, added.finished_on, memory_store.list_books()) == (
        transform.Status.FINISHED,
        today,
        [added],
    )


def test_when_edit_book_then_added_date_kept(
    memory_store: MemoryStore, make_draft: MakeDraft, today: datetime.date
) -> None:
    added = operate.add_book(
        make_draft(), store=memory_store, today=datetime.date(2026, 1, 1)
    )
    edited = operate.edit_book(
        added.id, make_draft(title="Changed"), store=memory_store, today=today
    )
    assert (edited.title, edited.added_on) == ("Changed", datetime.date(2026, 1, 1))


def test_when_record_progress_then_status_follows(
    memory_store: MemoryStore, make_draft: MakeDraft, today: datetime.date
) -> None:
    added = operate.add_book(make_draft(), store=memory_store, today=today)
    updated = operate.record_progress(
        added.id,
        pages_read=50,
        status=transform.Status.TO_READ,
        store=memory_store,
        today=today,
    )
    assert operate.get_book(added.id, store=memory_store) == updated
    assert updated.status is transform.Status.READING


def test_when_record_progress_past_end_then_invalid(
    memory_store: MemoryStore, make_draft: MakeDraft, today: datetime.date
) -> None:
    added = operate.add_book(make_draft(), store=memory_store, today=today)
    with pytest.raises(error.InvalidError):
        operate.record_progress(
            added.id,
            pages_read=301,
            status=transform.Status.READING,
            store=memory_store,
            today=today,
        )


def test_when_delete_book_then_gone(
    memory_store: MemoryStore, make_draft: MakeDraft, today: datetime.date
) -> None:
    added = operate.add_book(make_draft(), store=memory_store, today=today)
    operate.delete_book(added.id, store=memory_store)
    assert memory_store.list_books() == []


def test_when_browse_then_matching_books_in_order(
    memory_store: MemoryStore, make_draft: MakeDraft, today: datetime.date
) -> None:
    for title in ["Beta", "Alpha", "Gamma"]:
        operate.add_book(make_draft(title=title), store=memory_store, today=today)
    found = operate.browse(
        order=transform.Order.TITLE, query="a", status=None, store=memory_store
    )
    assert [book.title for book in found] == ["Alpha", "Beta", "Gamma"]


def test_when_summarise_then_totals_from_store(
    memory_store: MemoryStore, make_draft: MakeDraft, today: datetime.date
) -> None:
    operate.add_book(make_draft(pages_read=10), store=memory_store, today=today)
    stats = operate.summarise(store=memory_store, today=today)
    assert (stats.total, stats.pages_read) == (1, 10)
