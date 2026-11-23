import datetime

from reading_list.code import transform


def test_when_summarise_then_counts_per_status(
    library: list[transform.Book], today: datetime.date
) -> None:
    stats = transform.summarise(library, today=today)
    assert stats.by_status == {
        transform.Status.TO_READ: 1,
        transform.Status.READING: 1,
        transform.Status.FINISHED: 3,
    }


def test_when_summarise_then_totals_add_up(
    library: list[transform.Book], today: datetime.date
) -> None:
    stats = transform.summarise(library, today=today)
    assert (
        stats.total,
        stats.finished_this_year,
        stats.pages_read,
        stats.average_rating,
        stats.rated,
    ) == (5, 2, 387 + 100 + 272, 4.5, 2)


def test_when_summarise_then_last_twelve_months_counted(
    library: list[transform.Book], today: datetime.date
) -> None:
    stats = transform.summarise(library, today=today)
    counted = {item.month: item.count for item in stats.finished_by_month}
    assert (
        next(iter(counted)),
        list(counted)[-1],
        len(counted),
        counted[datetime.date(2026, 2, 1)],
        counted[datetime.date(2026, 11, 1)],
        sum(counted.values()),
    ) == (datetime.date(2025, 12, 1), datetime.date(2026, 11, 1), 12, 1, 1, 2)


def test_when_summarise_january_then_months_cross_the_year() -> None:
    stats = transform.summarise([], today=datetime.date(2027, 1, 15))
    assert [item.month for item in stats.finished_by_month][:2] == [
        datetime.date(2026, 2, 1),
        datetime.date(2026, 3, 1),
    ]


def test_when_summarise_empty_then_zeros_and_no_rating(today: datetime.date) -> None:
    stats = transform.summarise([], today=today)
    assert (stats.total, stats.pages_read, stats.average_rating) == (0, 0, None)
