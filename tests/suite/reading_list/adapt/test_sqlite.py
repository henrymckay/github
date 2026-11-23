lazy import datetime
lazy import pathlib

import pytest

from reading_list.code import error, transform
from reading_list.code.adapt import sqlite_
lazy from pytest_.given import MakeDraft


def test_when_add_book_then_round_trips(
    sqlite_store: sqlite_.Store, make_draft: MakeDraft, today: datetime.date
) -> None:
    draft = make_draft(
        notes="Ünïcode ✓", pages=None, rating=5, status=transform.Status.FINISHED
    )
    added = sqlite_store.add_book(draft, added_on=today, finished_on=today)
    assert sqlite_store.list_books() == [added]
    assert transform.to_draft(added) == draft


def test_when_new_store_then_file_and_folder_created(
    sqlite_store: sqlite_.Store, db_path: pathlib.Path
) -> None:
    assert (sqlite_store.list_books(), db_path.exists()) == ([], True)


def test_when_save_book_then_replaced(
    sqlite_store: sqlite_.Store, make_draft: MakeDraft, today: datetime.date
) -> None:
    added = sqlite_store.add_book(make_draft(), added_on=today, finished_on=None)
    changed = transform.Book(
        added_on=added.added_on,
        author="Someone",
        finished_on=today,
        id=added.id,
        notes="n",
        pages=10,
        pages_read=10,
        rating=2,
        status=transform.Status.FINISHED,
        title="New",
    )
    sqlite_store.save_book(changed)
    assert sqlite_store.get_book(added.id) == changed


def test_when_delete_book_then_absent(
    sqlite_store: sqlite_.Store, make_draft: MakeDraft, today: datetime.date
) -> None:
    added = sqlite_store.add_book(make_draft(), added_on=today, finished_on=None)
    sqlite_store.delete_book(added.id)
    with pytest.raises(error.AbsentError):
        sqlite_store.get_book(added.id)


def test_when_delete_missing_then_absent(sqlite_store: sqlite_.Store) -> None:
    with pytest.raises(error.AbsentError):
        sqlite_store.delete_book(42)


def test_when_save_missing_then_absent(
    sqlite_store: sqlite_.Store, make_draft: MakeDraft, today: datetime.date
) -> None:
    added = sqlite_store.add_book(make_draft(), added_on=today, finished_on=None)
    with pytest.raises(error.AbsentError):
        sqlite_store.save_book(
            transform.Book(
                added_on=today,
                author="",
                finished_on=None,
                id=added.id + 1,
                notes="",
                pages=None,
                pages_read=0,
                rating=None,
                status=transform.Status.TO_READ,
                title="Ghost",
            )
        )


def test_when_reopened_then_books_persist(
    db_path: pathlib.Path, make_draft: MakeDraft, today: datetime.date
) -> None:
    sqlite_.Store(path=db_path).add_book(make_draft(), added_on=today, finished_on=None)
    assert len(sqlite_.Store(path=db_path).list_books()) == 1
