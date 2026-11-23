"""The JSON API's response bodies."""

lazy import datetime

import pydantic

from reading_list.code import transform


class BookOut(pydantic.BaseModel):
    """A book as the API returns it."""

    added_on: datetime.date
    author: str
    finished_on: datetime.date | None
    id: int
    notes: str
    pages: int | None
    pages_read: int
    progress: float | None
    rating: int | None
    status: transform.Status
    title: str


class MonthOut(pydantic.BaseModel):
    """Books finished in one month."""

    count: int
    month: str


class StatsOut(pydantic.BaseModel):
    """The library's totals."""

    average_rating: float | None
    by_status: dict[transform.Status, int]
    finished_by_month: list[MonthOut]
    finished_this_year: int
    pages_read: int
    total: int


def to_book_out(book: transform.Book) -> BookOut:
    """Return the API body for a book."""
    return BookOut(
        added_on=book.added_on,
        author=book.author,
        finished_on=book.finished_on,
        id=book.id,
        notes=book.notes,
        pages=book.pages,
        pages_read=book.pages_read,
        progress=transform.pick_progress(book),
        rating=book.rating,
        status=book.status,
        title=book.title,
    )


def to_stats_out(stats: transform.Stats) -> StatsOut:
    """Return the API body for the stats."""
    return StatsOut(
        average_rating=stats.average_rating,
        by_status=stats.by_status,
        finished_by_month=[
            MonthOut(count=item.count, month=f"{item.month:%Y-%m}")
            for item in stats.finished_by_month
        ],
        finished_this_year=stats.finished_this_year,
        pages_read=stats.pages_read,
        total=stats.total,
    )
