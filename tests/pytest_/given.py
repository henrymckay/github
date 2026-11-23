import collections.abc
import copy
import dataclasses
import datetime
lazy import pathlib

import fastapi.testclient
import pytest

from reading_list.code import error, transform
from reading_list.code.adapt import sqlite_
from reading_list.code.drive.fastapi_ import build_app, provide

type MakeDraft = collections.abc.Callable[..., transform.Draft]
type MakeBook = collections.abc.Callable[..., transform.Book]


@dataclasses.dataclass(kw_only=True)
class MemoryStore:
    books: dict[int, transform.Book] = dataclasses.field(
        default_factory=dict[int, transform.Book]
    )

    def add_book(
        self,
        draft: transform.Draft,
        *,
        added_on: datetime.date,
        finished_on: datetime.date | None,
    ) -> transform.Book:
        book_id = max(self.books, default=0) + 1
        book = transform.Book(
            added_on=added_on,
            author=draft.author,
            finished_on=finished_on,
            id=book_id,
            notes=draft.notes,
            pages=draft.pages,
            pages_read=draft.pages_read,
            rating=draft.rating,
            status=draft.status,
            title=draft.title,
        )
        self.books[book_id] = book
        return book

    def delete_book(self, book_id: int) -> None:
        if self.books.pop(book_id, None) is None:
            raise error.AbsentError(book_id)

    def get_book(self, book_id: int) -> transform.Book:
        if book_id not in self.books:
            raise error.AbsentError(book_id)
        return self.books[book_id]

    def list_books(self) -> list[transform.Book]:
        return list(self.books.values())

    def save_book(self, book: transform.Book) -> None:
        self.get_book(book.id)
        self.books[book.id] = book


@pytest.fixture
def today() -> datetime.date:
    return datetime.date(2026, 11, 23)


@pytest.fixture
def make_draft() -> MakeDraft:
    base = transform.Draft(
        author="Ursula K. Le Guin",
        notes="",
        pages=300,
        pages_read=0,
        rating=None,
        status=transform.Status.TO_READ,
        title="The Dispossessed",
    )

    def make(**changes: object) -> transform.Draft:
        return copy.replace(base, **changes)

    return make


@pytest.fixture
def make_book(today: datetime.date) -> MakeBook:
    base = transform.Book(
        added_on=today,
        author="Ursula K. Le Guin",
        finished_on=None,
        id=1,
        notes="",
        pages=300,
        pages_read=0,
        rating=None,
        status=transform.Status.TO_READ,
        title="The Dispossessed",
    )

    def make(**changes: object) -> transform.Book:
        return copy.replace(base, **changes)

    return make


@pytest.fixture
def library(make_book: MakeBook, today: datetime.date) -> list[transform.Book]:
    return [
        make_book(
            id=1,
            title="The Dispossessed",
            author="Ursula K. Le Guin",
            added_on=datetime.date(2026, 1, 5),
            pages=387,
            pages_read=387,
            status=transform.Status.FINISHED,
            finished_on=datetime.date(2026, 2, 10),
            rating=5,
        ),
        make_book(
            id=2,
            title="dune",
            author="Frank Herbert",
            added_on=datetime.date(2026, 3, 1),
            pages=412,
            pages_read=100,
            status=transform.Status.READING,
            notes="Spice and sandworms",
        ),
        make_book(
            id=3,
            title="Middlemarch",
            author="George Eliot",
            added_on=datetime.date(2026, 3, 1),
            pages=None,
            pages_read=0,
            status=transform.Status.TO_READ,
        ),
        make_book(
            id=4,
            title="A Wizard of Earthsea",
            author="Ursula K. Le Guin",
            added_on=datetime.date(2025, 6, 1),
            pages=None,
            pages_read=0,
            status=transform.Status.FINISHED,
            finished_on=datetime.date(2025, 11, 30),
            rating=4,
        ),
        make_book(
            id=5,
            title="Piranesi",
            author="Susanna Clarke",
            added_on=today,
            pages=272,
            pages_read=272,
            status=transform.Status.FINISHED,
            finished_on=today,
        ),
    ]


@pytest.fixture
def memory_store() -> MemoryStore:
    return MemoryStore()


@pytest.fixture
def db_path(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path.joinpath("data", "books.db")


@pytest.fixture
def sqlite_store(db_path: pathlib.Path) -> sqlite_.Store:
    return sqlite_.Store(path=db_path)


@pytest.fixture
def client(
    db_path: pathlib.Path, today: datetime.date
) -> collections.abc.Iterator[fastapi.testclient.TestClient]:
    app = build_app(db=db_path)
    app.dependency_overrides[provide.read_today] = lambda: today
    with fastapi.testclient.TestClient(app, base_url="http://127.0.0.1") as test_client:
        yield test_client
