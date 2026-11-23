"""Totals over the library for the stats screen."""

import dataclasses
import datetime
import statistics
lazy import collections.abc

from reading_list.code.transform import book

_MONTHS = 12


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class MonthCount:
    """How many books were finished in one calendar month."""

    count: int
    month: datetime.date


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Stats:
    """The library summarised."""

    average_rating: float | None
    by_status: dict[book.Status, int]
    finished_by_month: tuple[MonthCount, ...]
    finished_this_year: int
    pages_read: int
    rated: int
    total: int


def _shift_month(month: datetime.date, *, by: int) -> datetime.date:
    index = month.year * 12 + month.month - 1 + by
    return datetime.date(index // 12, index % 12 + 1, 1)


def summarise(
    books: collections.abc.Iterable[book.Book], *, today: datetime.date
) -> Stats:
    """Return the library's totals as of today.

    :param books: The library.
    :param today: The date the year and the last twelve months are counted to.
    :returns: Counts per status, books finished this year and per month over
        the last twelve months, pages read in total and the average rating.
    """
    items = list(books)
    finished = [item.finished_on for item in items if item.finished_on is not None]
    this_month = today.replace(day=1)
    months = [_shift_month(this_month, by=-back) for back in reversed(range(_MONTHS))]
    ratings = [item.rating for item in items if item.rating is not None]
    return Stats(
        average_rating=statistics.fmean(ratings) if ratings else None,
        by_status={
            status: sum(1 for item in items if item.status is status)
            for status in book.Status
        },
        finished_by_month=tuple(
            MonthCount(
                count=sum(1 for day in finished if day.replace(day=1) == month),
                month=month,
            )
            for month in months
        ),
        finished_this_year=sum(1 for day in finished if day.year == today.year),
        pages_read=sum(item.pages_read for item in items),
        rated=len(ratings),
        total=len(items),
    )
