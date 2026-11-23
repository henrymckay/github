"""The screens and API routes — the composition root for each request."""

import datetime
import typing
import urllib.parse

import fastapi
import fastapi.responses

from reading_list.code import error, operate, port, transform
from reading_list.code.drive.fastapi_ import provide, render, schema

router = fastapi.APIRouter()
templates = render.build_templates()

type Store = typing.Annotated[port.Store, fastapi.Depends(provide.store)]
type Today = typing.Annotated[datetime.date, fastapi.Depends(provide.read_today)]
type Text = typing.Annotated[str, fastapi.Form()]

_CHART_HEIGHT: typing.Final = 140


def _parse_order(text: str) -> transform.Order:
    try:
        return transform.Order(text)
    except ValueError:
        return transform.Order.RECENT


def _parse_status(text: str) -> transform.Status | None:
    try:
        return transform.Status(text)
    except ValueError:
        return None


def _build_back(*, order: str, query: str, status: str) -> str:
    kept = {
        key: value
        for key, value in {"q": query, "status": status, "sort": order}.items()
        if value
    }
    return f"/?{urllib.parse.urlencode(kept)}" if kept else "/"


def _render_library(
    request: fastapi.Request,
    *,
    store: port.Store,
    form: dict[str, str] | None = None,
    order: str = "",
    problems: dict[str, str] | None = None,
    query: str = "",
    row_problem: tuple[int, str] | None = None,
    status: str = "",
    status_code: int = 200,
) -> fastapi.responses.HTMLResponse:
    chosen_status = _parse_status(status)
    chosen_order = _parse_order(order)
    books = operate.browse(
        order=chosen_order, query=query.strip(), status=chosen_status, store=store
    )
    return templates.TemplateResponse(
        request,
        "library.html",
        {
            "back": _build_back(order=order, query=query, status=status),
            "books": books,
            "form": form or {},
            "order": chosen_order,
            "problems": problems or {},
            "query": query,
            "row_problem": row_problem,
            "searching": bool(query.strip()) or chosen_status is not None,
            "status": chosen_status,
            "total": len(store.list_books()),
        },
        status_code=status_code,
    )


@router.get("/", response_class=fastapi.responses.HTMLResponse)
def show_library(
    request: fastapi.Request,
    store: Store,
    q: str = "",
    sort: str = "",
    status: str = "",
) -> fastapi.responses.HTMLResponse:
    """Show the library, searched, filtered and sorted."""
    return _render_library(request, order=sort, query=q, status=status, store=store)


@router.post("/books", response_model=None)
def add_book(
    request: fastapi.Request,
    store: Store,
    today: Today,
    title: Text = "",
    author: Text = "",
    pages: Text = "",
    pages_read: Text = "",
    status: Text = "",
    rating: Text = "",
    notes: Text = "",
) -> fastapi.responses.Response:
    """Add a book, then show it in the library."""
    form = {
        "author": author,
        "notes": notes,
        "pages": pages,
        "pages_read": pages_read,
        "rating": rating,
        "status": status,
        "title": title,
    }
    try:
        added = operate.add_book(transform.parse_draft(form), store=store, today=today)
    except error.InvalidError as failure:
        return _render_library(
            request,
            form=form,
            problems=failure.problems,
            status_code=422,
            store=store,
        )
    return fastapi.responses.RedirectResponse(f"/#book-{added.id}", status_code=303)


@router.get("/books/{book_id}", response_class=fastapi.responses.HTMLResponse)
def show_book(
    request: fastapi.Request, book_id: int, store: Store
) -> fastapi.responses.HTMLResponse:
    """Show the edit screen for one book."""
    book = operate.get_book(book_id, store=store)
    form = {
        "author": book.author,
        "notes": book.notes,
        "pages": "" if book.pages is None else str(book.pages),
        "pages_read": str(book.pages_read),
        "rating": "" if book.rating is None else str(book.rating),
        "status": book.status.value,
        "title": book.title,
    }
    return templates.TemplateResponse(
        request, "edit.html", {"book": book, "form": form, "problems": {}}
    )


@router.post("/books/{book_id}", response_model=None)
def edit_book(
    request: fastapi.Request,
    book_id: int,
    store: Store,
    today: Today,
    title: Text = "",
    author: Text = "",
    pages: Text = "",
    pages_read: Text = "",
    status: Text = "",
    rating: Text = "",
    notes: Text = "",
) -> fastapi.responses.Response:
    """Save a book's details, then show it in the library."""
    book = operate.get_book(book_id, store=store)
    form = {
        "author": author,
        "notes": notes,
        "pages": pages,
        "pages_read": pages_read,
        "rating": rating,
        "status": status,
        "title": title,
    }
    try:
        operate.edit_book(
            book_id, transform.parse_draft(form), store=store, today=today
        )
    except error.InvalidError as failure:
        return templates.TemplateResponse(
            request,
            "edit.html",
            {"book": book, "form": form, "problems": failure.problems},
            status_code=422,
        )
    return fastapi.responses.RedirectResponse(f"/#book-{book_id}", status_code=303)


@router.post("/books/{book_id}/progress", response_model=None)
def record_progress(
    request: fastapi.Request,
    book_id: int,
    store: Store,
    today: Today,
    pages_read: Text = "",
    status: Text = "",
    back: Text = "/",
) -> fastapi.responses.Response:
    """Record pages read and status from the library row."""
    book = operate.get_book(book_id, store=store)
    target = back if back.startswith("/") and not back.startswith("//") else "/"
    try:
        parsed = transform.parse_draft(
            {
                "pages": "" if book.pages is None else str(book.pages),
                "pages_read": pages_read.strip() or str(book.pages_read),
                "status": status or book.status.value,
                "title": book.title,
            }
        )
        operate.record_progress(
            book_id,
            pages_read=parsed.pages_read,
            status=parsed.status,
            store=store,
            today=today,
        )
    except error.InvalidError as failure:
        kept = urllib.parse.parse_qs(urllib.parse.urlsplit(target).query)
        return _render_library(
            request,
            order=kept.get("sort", [""])[0],
            query=kept.get("q", [""])[0],
            row_problem=(book_id, str(failure)),
            status=kept.get("status", [""])[0],
            status_code=422,
            store=store,
        )
    return fastapi.responses.RedirectResponse(
        f"{target}#book-{book_id}", status_code=303
    )


@router.post("/books/{book_id}/delete")
def delete_book(book_id: int, store: Store) -> fastapi.responses.RedirectResponse:
    """Delete a book, then show the library."""
    operate.delete_book(book_id, store=store)
    return fastapi.responses.RedirectResponse("/", status_code=303)


def _build_bars(stats: transform.Stats) -> list[dict[str, object]]:
    tallest = max((item.count for item in stats.finished_by_month), default=0)
    return [
        {
            "count": item.count,
            "height": round(item.count / tallest * _CHART_HEIGHT) if tallest else 0,
            "label": f"{item.month:%b}",
            "title": f"{item.month:%B %Y}",
        }
        for item in stats.finished_by_month
    ]


@router.get("/stats", response_class=fastapi.responses.HTMLResponse)
def show_stats(
    request: fastapi.Request, store: Store, today: Today
) -> fastapi.responses.HTMLResponse:
    """Show the library's totals."""
    stats = operate.summarise(store=store, today=today)
    return templates.TemplateResponse(
        request,
        "stats.html",
        {
            "bars": _build_bars(stats),
            "stats": stats,
            "today": today,
        },
    )


@router.get("/api/books")
def list_books(
    store: Store, q: str = "", sort: str = "", status: str = ""
) -> list[schema.BookOut]:
    """Return the library as JSON, with the same search as the library screen."""
    books = operate.browse(
        order=_parse_order(sort),
        query=q.strip(),
        status=_parse_status(status),
        store=store,
    )
    return [schema.to_book_out(book) for book in books]


@router.get("/api/books/{book_id}")
def get_book(book_id: int, store: Store) -> schema.BookOut:
    """Return one book as JSON."""
    return schema.to_book_out(operate.get_book(book_id, store=store))


@router.get("/api/stats")
def get_stats(store: Store, today: Today) -> schema.StatsOut:
    """Return the library's totals as JSON."""
    return schema.to_stats_out(operate.summarise(store=store, today=today))
