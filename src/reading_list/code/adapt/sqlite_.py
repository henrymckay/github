"""The store, as one SQLite file."""

import contextlib
import dataclasses
import datetime
import sqlite3
import typing
lazy import collections.abc
lazy import pathlib

from reading_list.code import error, transform

_SCHEMA: typing.Final = """
create table if not exists book (
    id integer primary key,
    title text not null,
    author text not null default '',
    pages integer,
    pages_read integer not null default 0,
    status text not null,
    rating integer,
    notes text not null default '',
    added_on text not null,
    finished_on text
)
"""

_COLUMNS: typing.Final = (
    "id, title, author, pages, pages_read, status, rating, notes, added_on, finished_on"
)


def _parse_row(row: sqlite3.Row) -> transform.Book:
    finished_on: str | None = row["finished_on"]
    return transform.Book(
        added_on=datetime.date.fromisoformat(row["added_on"]),
        author=row["author"],
        finished_on=(datetime.date.fromisoformat(finished_on) if finished_on else None),
        id=row["id"],
        notes=row["notes"],
        pages=row["pages"],
        pages_read=row["pages_read"],
        rating=row["rating"],
        status=transform.Status(row["status"]),
        title=row["title"],
    )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Store:
    """Books kept in one SQLite file, created on first use."""

    path: pathlib.Path

    @contextlib.contextmanager
    def _connect(self) -> collections.abc.Generator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with contextlib.closing(sqlite3.connect(self.path)) as connection:
            connection.row_factory = sqlite3.Row
            with connection:
                connection.execute(_SCHEMA)
                yield connection

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
        with self._connect() as connection:
            cursor = connection.execute(
                "insert into book (title, author, pages, pages_read, status, "
                "rating, notes, added_on, finished_on) "
                "values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    draft.title,
                    draft.author,
                    draft.pages,
                    draft.pages_read,
                    draft.status.value,
                    draft.rating,
                    draft.notes,
                    added_on.isoformat(),
                    finished_on.isoformat() if finished_on else None,
                ),
            )
            book_id = cursor.lastrowid
        assert book_id is not None
        return self.get_book(book_id)

    def delete_book(self, book_id: int) -> None:
        """Remove a book.

        :param book_id: The book's id.
        :raises error.AbsentError: If there is no such book.
        """
        with self._connect() as connection:
            cursor = connection.execute("delete from book where id = ?", (book_id,))
        if cursor.rowcount == 0:
            raise error.AbsentError(f"No book with id {book_id}.")

    def get_book(self, book_id: int) -> transform.Book:
        """Return one book.

        :param book_id: The book's id.
        :returns: The book.
        :raises error.AbsentError: If there is no such book.
        """
        with self._connect() as connection:
            row = connection.execute(
                f"select {_COLUMNS} from book where id = ?", (book_id,)
            ).fetchone()
        if row is None:
            raise error.AbsentError(f"No book with id {book_id}.")
        return _parse_row(row)

    def list_books(self) -> list[transform.Book]:
        """Return every book, in no particular order.

        :returns: The library.
        """
        with self._connect() as connection:
            rows = connection.execute(f"select {_COLUMNS} from book").fetchall()
        return [_parse_row(row) for row in rows]

    def save_book(self, book: transform.Book) -> None:
        """Overwrite a stored book.

        :param book: The book, carrying the id of the one it replaces.
        :raises error.AbsentError: If there is no such book.
        """
        with self._connect() as connection:
            cursor = connection.execute(
                "update book set title = ?, author = ?, pages = ?, pages_read = ?, "
                "status = ?, rating = ?, notes = ?, added_on = ?, finished_on = ? "
                "where id = ?",
                (
                    book.title,
                    book.author,
                    book.pages,
                    book.pages_read,
                    book.status.value,
                    book.rating,
                    book.notes,
                    book.added_on.isoformat(),
                    book.finished_on.isoformat() if book.finished_on else None,
                    book.id,
                ),
            )
        if cursor.rowcount == 0:
            raise error.AbsentError(f"No book with id {book.id}.")
