import datetime
from typing import TYPE_CHECKING

import pytest

from reading_list.code import error, transform

if TYPE_CHECKING:
    from pytest_.given import MakeBook, MakeDraft

Status = transform.Status


def test_when_parse_full_form_then_draft_holds_typed_values() -> None:
    draft = transform.parse_draft(
        {
            "author": " Frank Herbert ",
            "notes": " Spice ",
            "pages": "412",
            "pages_read": "100",
            "rating": "4",
            "status": "reading",
            "title": " Dune ",
        }
    )
    assert draft == transform.Draft(
        author="Frank Herbert",
        notes="Spice",
        pages=412,
        pages_read=100,
        rating=4,
        status=Status.READING,
        title="Dune",
    )


def test_when_parse_title_only_then_defaults_fill_the_rest() -> None:
    draft = transform.parse_draft({"title": "Dune"})
    assert (draft.pages, draft.pages_read, draft.rating, draft.status) == (
        None,
        0,
        None,
        Status.TO_READ,
    )


@pytest.mark.parametrize(
    ("fields", "field"),
    argvalues=[
        ({"title": ""}, "title"),
        ({"title": "x" * 301}, "title"),
        ({"title": "Dune", "notes": "x" * 5001}, "notes"),
        ({"title": "Dune", "pages": "lots"}, "pages"),
        ({"title": "Dune", "pages": "-3"}, "pages"),
        ({"title": "Dune", "pages": "0"}, "pages"),
        ({"title": "Dune", "pages": "10", "pages_read": "11"}, "pages_read"),
        ({"title": "Dune", "rating": "6"}, "rating"),
        ({"title": "Dune", "pages": "1000001"}, "pages"),
        ({"title": "Dune", "rating": "0"}, "rating"),
        ({"title": "Dune", "status": "lost"}, "status"),
    ],
)
def test_when_parse_bad_field_then_invalid_names_it(
    fields: dict[str, str], field: str
) -> None:
    with pytest.raises(error.InvalidError) as raised:
        transform.parse_draft(fields)
    assert list(raised.value.problems) == [field]


def test_when_check_negative_pages_read_then_invalid(make_draft: MakeDraft) -> None:
    with pytest.raises(error.InvalidError, match="negative"):
        transform.check_draft(make_draft(pages_read=-1))


@pytest.mark.parametrize(
    ("pages", "pages_read", "expected"),
    argvalues=[(200, 50, 0.25), (200, 200, 1.0), (None, 30, None)],
)
def test_when_pick_progress_then_pages_read_over_pages(
    make_book: MakeBook, pages: int | None, pages_read: int, expected: float | None
) -> None:
    assert transform.pick_progress(make_book(pages=pages, pages_read=pages_read)) == (
        expected
    )


@pytest.mark.parametrize(
    ("status", "pages", "pages_read", "expected_status", "expected_read"),
    argvalues=[
        (Status.TO_READ, 300, 0, Status.TO_READ, 0),
        (Status.TO_READ, 300, 20, Status.READING, 20),
        (Status.TO_READ, 300, 300, Status.FINISHED, 300),
        (Status.READING, None, 50, Status.READING, 50),
        (Status.FINISHED, None, 0, Status.FINISHED, 0),
    ],
)
def test_when_settle_new_book_then_progress_decides_status(
    make_draft: MakeDraft,
    today: datetime.date,
    status: Status,
    pages: int | None,
    pages_read: int,
    expected_status: Status,
    expected_read: int,
) -> None:
    settled, _ = transform.settle(
        make_draft(status=status, pages=pages, pages_read=pages_read),
        before=None,
        today=today,
    )
    assert (settled.status, settled.pages_read) == (expected_status, expected_read)


def test_when_settle_new_finished_book_then_stamped_today(
    make_draft: MakeDraft, today: datetime.date
) -> None:
    settled, finished_on = transform.settle(
        make_draft(status=Status.FINISHED), before=None, today=today
    )
    assert (settled.pages_read, finished_on) == (300, today)


def test_when_settle_unfinished_then_no_finish_date(
    make_draft: MakeDraft, today: datetime.date
) -> None:
    _, finished_on = transform.settle(make_draft(), before=None, today=today)
    assert finished_on is None


def test_when_choose_finished_then_every_page_read(
    make_draft: MakeDraft, make_book: MakeBook, today: datetime.date
) -> None:
    settled, finished_on = transform.settle(
        make_draft(status=Status.FINISHED, pages_read=40),
        before=make_book(status=Status.READING, pages_read=40),
        today=today,
    )
    assert (settled.pages_read, finished_on) == (300, today)


def test_when_choose_finished_without_page_count_then_pages_read_kept(
    make_draft: MakeDraft, make_book: MakeBook, today: datetime.date
) -> None:
    settled, _ = transform.settle(
        make_draft(status=Status.FINISHED, pages=None, pages_read=40),
        before=make_book(status=Status.READING, pages=None, pages_read=40),
        today=today,
    )
    assert settled.pages_read == 40


def test_when_reopen_fully_read_book_then_starts_from_zero(
    make_draft: MakeDraft, make_book: MakeBook, today: datetime.date
) -> None:
    settled, finished_on = transform.settle(
        make_draft(status=Status.READING, pages_read=300),
        before=make_book(
            status=Status.FINISHED,
            pages_read=300,
            finished_on=datetime.date(2026, 1, 1),
        ),
        today=today,
    )
    assert (settled.status, settled.pages_read, finished_on) == (
        Status.READING,
        0,
        None,
    )


def test_when_choose_to_read_with_pages_read_then_choice_honoured(
    make_draft: MakeDraft, make_book: MakeBook, today: datetime.date
) -> None:
    settled, _ = transform.settle(
        make_draft(status=Status.TO_READ, pages_read=40),
        before=make_book(status=Status.READING, pages_read=40),
        today=today,
    )
    assert (settled.status, settled.pages_read) == (Status.TO_READ, 40)


def test_when_choose_reading_with_every_page_read_then_finished(
    make_draft: MakeDraft, make_book: MakeBook, today: datetime.date
) -> None:
    settled, finished_on = transform.settle(
        make_draft(status=Status.READING, pages_read=300),
        before=make_book(status=Status.TO_READ, pages_read=0),
        today=today,
    )
    assert (settled.status, finished_on) == (Status.FINISHED, today)


def test_when_finished_book_page_count_raised_then_stays_finished(
    make_draft: MakeDraft, make_book: MakeBook, today: datetime.date
) -> None:
    first = datetime.date(2026, 1, 1)
    settled, finished_on = transform.settle(
        make_draft(status=Status.FINISHED, pages=310, pages_read=300),
        before=make_book(status=Status.FINISHED, pages_read=300, finished_on=first),
        today=today,
    )
    assert (settled.status, settled.pages_read, finished_on) == (
        Status.FINISHED,
        310,
        first,
    )


def test_when_lower_progress_on_finished_book_then_reading_again(
    make_draft: MakeDraft, make_book: MakeBook, today: datetime.date
) -> None:
    settled, finished_on = transform.settle(
        make_draft(status=Status.FINISHED, pages_read=120),
        before=make_book(
            status=Status.FINISHED,
            pages_read=300,
            finished_on=datetime.date(2026, 1, 1),
        ),
        today=today,
    )
    assert (settled.status, finished_on) == (Status.READING, None)


def test_when_edit_finished_book_then_finish_date_kept(
    make_draft: MakeDraft, make_book: MakeBook, today: datetime.date
) -> None:
    first = datetime.date(2026, 1, 1)
    _, finished_on = transform.settle(
        make_draft(status=Status.FINISHED, pages_read=300, notes="Loved it"),
        before=make_book(status=Status.FINISHED, pages_read=300, finished_on=first),
        today=today,
    )
    assert finished_on == first


def test_when_to_draft_then_editable_fields_kept(make_book: MakeBook) -> None:
    book = make_book(notes="n", rating=3, pages_read=10, status=Status.READING)
    assert transform.to_draft(book) == transform.Draft(
        author=book.author,
        notes="n",
        pages=300,
        pages_read=10,
        rating=3,
        status=Status.READING,
        title=book.title,
    )


def test_when_status_label_then_sentence_case() -> None:
    assert [status.label for status in Status] == ["To read", "Reading", "Finished"]
