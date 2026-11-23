"""What the core needs the outside world to provide."""

import typing
lazy import datetime

lazy from reading_list.code import transform


class Store(typing.Protocol):
    """Where the books are kept."""

    def add_book(
        self,
        draft: transform.Draft,
        *,
        added_on: datetime.date,
        finished_on: datetime.date | None,
    ) -> transform.Book:
        """Store a new book and return it with its id.

        :param draft: The settled draft.
        :param added_on: The day it was added.
        :param finished_on: The day it was finished, or None.
        :returns: The stored book.
        """
        ...

    def delete_book(self, book_id: int) -> None:
        """Remove a book.

        :param book_id: The book's id.
        :raises error.AbsentError: If there is no such book.
        """
        ...

    def get_book(self, book_id: int) -> transform.Book:
        """Return one book.

        :param book_id: The book's id.
        :returns: The book.
        :raises error.AbsentError: If there is no such book.
        """
        ...

    def list_books(self) -> list[transform.Book]:
        """Return every book, in no particular order.

        :returns: The library.
        """
        ...

    def save_book(self, book: transform.Book) -> None:
        """Overwrite a stored book.

        :param book: The book, carrying the id of the one it replaces.
        :raises error.AbsentError: If there is no such book.
        """
        ...
