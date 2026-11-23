"""Adding, changing, finding and summarising books."""

import copy
lazy import datetime

from reading_list.code import port, transform


def add_book(
    draft: transform.Draft, *, store: port.Store, today: datetime.date
) -> transform.Book:
    """Add a book to the list.

    :param draft: What the person entered.
    :param store: Where books are kept.
    :param today: The day it is added.
    :returns: The stored book.
    """
    settled, finished_on = transform.settle(draft, before=None, today=today)
    return store.add_book(settled, added_on=today, finished_on=finished_on)


def browse(
    *,
    order: transform.Order,
    query: str,
    status: transform.Status | None,
    store: port.Store,
) -> list[transform.Book]:
    """Return the books matching a search, in order.

    :param order: How to order them.
    :param query: Words to find; empty finds every book.
    :param status: The status to keep, or None for all.
    :param store: Where books are kept.
    :returns: The matching books.
    """
    found = transform.keep_matching(store.list_books(), query=query, status=status)
    return transform.sort_books(found, order=order)


def delete_book(book_id: int, *, store: port.Store) -> None:
    """Remove a book from the list.

    :param book_id: The book's id.
    :param store: Where books are kept.
    """
    store.delete_book(book_id)


def edit_book(
    book_id: int,
    draft: transform.Draft,
    *,
    store: port.Store,
    today: datetime.date,
) -> transform.Book:
    """Replace a book's details.

    :param book_id: The book's id.
    :param draft: The new details.
    :param store: Where books are kept.
    :param today: The day a book finished now is stamped with.
    :returns: The stored book.
    """
    before = store.get_book(book_id)
    settled, finished_on = transform.settle(draft, before=before, today=today)
    after = transform.Book(
        added_on=before.added_on,
        author=settled.author,
        finished_on=finished_on,
        id=before.id,
        notes=settled.notes,
        pages=settled.pages,
        pages_read=settled.pages_read,
        rating=settled.rating,
        status=settled.status,
        title=settled.title,
    )
    store.save_book(after)
    return after


def get_book(book_id: int, *, store: port.Store) -> transform.Book:
    """Return one book.

    :param book_id: The book's id.
    :param store: Where books are kept.
    :returns: The book.
    """
    return store.get_book(book_id)


def record_progress(
    book_id: int,
    *,
    pages_read: int,
    status: transform.Status,
    store: port.Store,
    today: datetime.date,
) -> transform.Book:
    """Record how far a book has been read and where it stands.

    :param book_id: The book's id.
    :param pages_read: Pages read so far.
    :param status: The status the person picked.
    :param store: Where books are kept.
    :param today: The day a book finished now is stamped with.
    :returns: The stored book.
    :raises error.InvalidError: If the pages read break a rule.
    """
    before = store.get_book(book_id)
    draft = transform.check_draft(
        copy.replace(transform.to_draft(before), pages_read=pages_read, status=status)
    )
    return edit_book(book_id, draft, store=store, today=today)


def summarise(*, store: port.Store, today: datetime.date) -> transform.Stats:
    """Return the library's totals.

    :param store: Where books are kept.
    :param today: The date totals are counted to.
    :returns: The totals.
    """
    return transform.summarise(store.list_books(), today=today)
