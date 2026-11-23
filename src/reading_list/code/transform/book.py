"""A book on the list, the draft a form produces, and how status follows progress."""

import copy
import dataclasses
import enum
lazy import collections.abc
lazy import datetime

from reading_list.code import error

_TITLE_LIMIT = 300
_NOTES_LIMIT = 5000
_COUNT_LIMIT = 1_000_000


class Status(enum.StrEnum):
    """Where a book stands."""

    TO_READ = "to_read"
    READING = "reading"
    FINISHED = "finished"

    @property
    def label(self) -> str:
        """Return the status as a person reads it."""
        return self.value.replace("_", " ").capitalize()


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Draft:
    """What a person entered for a book, before the store gives it an id."""

    author: str
    notes: str
    pages: int | None
    pages_read: int
    rating: int | None
    status: Status
    title: str


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Book:
    """A book on the list."""

    added_on: datetime.date
    author: str
    finished_on: datetime.date | None
    id: int
    notes: str
    pages: int | None
    pages_read: int
    rating: int | None
    status: Status
    title: str


def _parse_count(
    text: str, *, field: str, label: str, problems: dict[str, str]
) -> int | None:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        value = int(stripped)
    except ValueError:
        problems[field] = f"{label} must be a whole number."
        return None
    if value < 0:
        problems[field] = f"{label} can't be negative."
        return None
    if value > _COUNT_LIMIT:
        problems[field] = f"{label} must be at most {_COUNT_LIMIT:,}."
        return None
    return value


def check_draft(draft: Draft) -> Draft:
    """Return the draft unchanged if it keeps every rule.

    :param draft: The draft to check.
    :returns: The same draft.
    :raises error.InvalidError: Naming each field that breaks a rule.
    """
    problems: dict[str, str] = {}
    if not draft.title:
        problems["title"] = "Give the book a title."
    elif len(draft.title) > _TITLE_LIMIT:
        problems["title"] = f"Keep the title under {_TITLE_LIMIT} characters."
    if len(draft.notes) > _NOTES_LIMIT:
        problems["notes"] = f"Keep the notes under {_NOTES_LIMIT} characters."
    if draft.pages == 0:
        problems["pages"] = "Pages must be at least 1, or left blank."
    if draft.pages_read < 0:
        problems["pages_read"] = "Pages read can't be negative."
    elif draft.pages is not None and draft.pages_read > draft.pages:
        problems["pages_read"] = (
            f"Pages read can't be more than the book's {draft.pages} pages."
        )
    if draft.rating is not None and not 1 <= draft.rating <= 5:
        problems["rating"] = "Rating must be from 1 to 5."
    if problems:
        raise error.InvalidError(problems)
    return draft


def parse_draft(fields: collections.abc.Mapping[str, str]) -> Draft:
    """Return the draft a submitted form describes.

    :param fields: The form's fields as text; a missing field counts as empty.
    :returns: The checked draft.
    :raises error.InvalidError: Naming each field that is malformed or breaks a rule.
    """
    problems: dict[str, str] = {}
    pages = _parse_count(
        fields.get("pages", ""), field="pages", label="Pages", problems=problems
    )
    pages_read = _parse_count(
        fields.get("pages_read", ""),
        field="pages_read",
        label="Pages read",
        problems=problems,
    )
    rating = _parse_count(
        fields.get("rating", ""), field="rating", label="Rating", problems=problems
    )
    status_text = fields.get("status", "") or Status.TO_READ.value
    try:
        status = Status(status_text)
    except ValueError:
        problems["status"] = "Pick a status from the list."
        status = Status.TO_READ
    if problems:
        raise error.InvalidError(problems)
    return check_draft(
        Draft(
            author=fields.get("author", "").strip(),
            notes=fields.get("notes", "").strip(),
            pages=pages,
            pages_read=pages_read or 0,
            rating=rating,
            status=status,
            title=fields.get("title", "").strip(),
        )
    )


def pick_progress(book: Book | Draft) -> float | None:
    """Return the share of the book read, from 0 to 1, or None without a page count.

    :param book: The book or draft.
    :returns: Pages read over pages, or None when the page count is unknown.
    """
    if book.pages is None:
        return None
    return book.pages_read / book.pages


def _settle_chosen(draft: Draft, *, before: Book | None) -> Draft:
    if draft.status is Status.FINISHED:
        return copy.replace(draft, pages_read=draft.pages or draft.pages_read)
    reopened = before is not None and before.status is Status.FINISHED
    if reopened and draft.pages_read == draft.pages:
        return copy.replace(draft, pages_read=0)
    if not reopened and draft.status is Status.READING:
        return _settle_by_progress(draft, before=before)
    return draft


def _settle_by_progress(draft: Draft, *, before: Book | None) -> Draft:
    if draft.pages is not None and draft.pages_read >= draft.pages:
        return copy.replace(draft, status=Status.FINISHED)
    if draft.status is Status.FINISHED and draft.pages is not None:
        went_back = before is not None and draft.pages_read < before.pages_read
        if went_back:
            return copy.replace(draft, status=Status.READING)
        return copy.replace(draft, pages_read=draft.pages)
    if draft.status is Status.TO_READ and draft.pages_read > 0:
        return copy.replace(draft, status=Status.READING)
    return draft


def settle(
    draft: Draft, *, before: Book | None, today: datetime.date
) -> tuple[Draft, datetime.date | None]:
    """Return the draft with status and progress agreeing, and its finish date.

    A status the person changed, or a new book added as finished, is honoured:
    finishing fills the pages read, and leaving a finished book with every
    page read starts it again from 0.
    Otherwise progress decides: every page read finishes the book, some pages
    read start it, fewer pages read than before reopen a finished one, and a
    finished book whose page count changed stays finished with every page read.
    Choosing reading with every page read finishes the book too.

    :param draft: What the person entered.
    :param before: The book as stored, or None for a new book.
    :param today: The date a book finished now is stamped with.
    :returns: The settled draft and the date it was finished, None if it isn't.
    """
    chosen = (
        draft.status is Status.FINISHED
        if before is None
        else draft.status is not before.status
    )
    settled = (
        _settle_chosen(draft, before=before)
        if chosen
        else _settle_by_progress(draft, before=before)
    )
    if settled.status is not Status.FINISHED:
        return settled, None
    kept = before.finished_on if before is not None else None
    return settled, kept or today


def to_draft(book: Book) -> Draft:
    """Return the editable part of a stored book.

    :param book: The stored book.
    :returns: Its draft.
    """
    return Draft(
        author=book.author,
        notes=book.notes,
        pages=book.pages,
        pages_read=book.pages_read,
        rating=book.rating,
        status=book.status,
        title=book.title,
    )
