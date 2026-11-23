import pytest

from reading_list.code import transform


@pytest.mark.parametrize(
    ("query", "status", "expected"),
    argvalues=[
        ("", None, [1, 2, 3, 4, 5]),
        ("le guin", None, [1, 4]),
        ("DUNE", None, [2]),
        ("sandworms", None, [2]),
        ("guin wizard", None, [4]),
        ("guin", transform.Status.FINISHED, [1, 4]),
        ("", transform.Status.TO_READ, [3]),
        ("nothing like this", None, []),
    ],
)
def test_when_keep_matching_then_every_word_and_status_match(
    library: list[transform.Book],
    query: str,
    status: transform.Status | None,
    expected: list[int],
) -> None:
    found = transform.keep_matching(library, query=query, status=status)
    assert [book.id for book in found] == expected


@pytest.mark.parametrize(
    ("order", "expected"),
    argvalues=[
        (transform.Order.RECENT, [5, 3, 2, 1, 4]),
        (transform.Order.TITLE, [4, 2, 3, 5, 1]),
        (transform.Order.AUTHOR, [2, 3, 5, 4, 1]),
        (transform.Order.PROGRESS, [5, 1, 4, 2, 3]),
    ],
)
def test_when_sort_books_then_in_order_asked(
    library: list[transform.Book], order: transform.Order, expected: list[int]
) -> None:
    ordered = transform.sort_books(library, order=order)
    assert [book.id for book in ordered] == expected


def test_when_order_label_then_sentence_case() -> None:
    assert [order.label for order in transform.Order] == [
        "Recently added",
        "Title",
        "Author",
        "Progress",
    ]
