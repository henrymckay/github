"""Searching and ordering the library."""

import enum
import typing
lazy import collections.abc

from reading_list.code.transform import book


class Order(enum.StrEnum):
    """How the library is ordered."""

    RECENT = "recent"
    TITLE = "title"
    AUTHOR = "author"
    PROGRESS = "progress"

    @property
    def label(self) -> str:
        """Return the order as a person reads it."""
        return {
            Order.RECENT: "Recently added",
            Order.TITLE: "Title",
            Order.AUTHOR: "Author",
            Order.PROGRESS: "Progress",
        }[self]


def _matches(item: book.Book, *, terms: list[str]) -> bool:
    text = f"{item.title}\n{item.author}\n{item.notes}".casefold()
    return all(term in text for term in terms)


def keep_matching(
    books: collections.abc.Iterable[book.Book],
    *,
    query: str,
    status: book.Status | None,
) -> list[book.Book]:
    """Return the books matching every word of the query and the status.

    :param books: The library.
    :param query: Words to find in the title, author or notes, in any case.
    :param status: The status to keep, or None for every status.
    :returns: The matching books, in the order given.
    """
    terms = query.casefold().split()
    return [
        item
        for item in books
        if (status is None or item.status is status) and _matches(item, terms=terms)
    ]


def _progress_key(item: book.Book) -> float:
    shown = book.pick_progress(item)
    if shown is not None:
        return shown
    return 1.0 if item.status is book.Status.FINISHED else 0.0


def sort_books(
    books: collections.abc.Iterable[book.Book], *, order: Order
) -> list[book.Book]:
    """Return the books in the order asked for.

    :param books: The books to order.
    :param order: Recent puts the newest first, progress the furthest read first.
    :returns: The ordered books.
    """
    newest = sorted(books, key=lambda item: (item.added_on, item.id), reverse=True)
    match order:
        case Order.RECENT:
            return newest
        case Order.TITLE:
            return sorted(newest, key=lambda item: item.title.casefold())
        case Order.AUTHOR:
            return sorted(
                newest,
                key=lambda item: (item.author.casefold(), item.title.casefold()),
            )
        case Order.PROGRESS:
            return sorted(newest, key=_progress_key, reverse=True)
        case _:
            typing.assert_never(order)
