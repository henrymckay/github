import re

lazy import fastapi.testclient

_DUNE = {
    "author": "Frank Herbert",
    "pages": "412",
    "pages_read": "0",
    "status": "to_read",
    "title": "Dune",
}


def _add(client: fastapi.testclient.TestClient, **changes: str) -> str:
    response = client.post("/books", data=_DUNE | changes, follow_redirects=False)
    assert response.status_code == 303
    location = response.headers["location"]
    match = re.fullmatch(r"/#book-(\d+)", location)
    assert match is not None
    return match.group(1)


def test_when_library_empty_then_invites_first_book(
    client: fastapi.testclient.TestClient,
) -> None:
    page = client.get("/")
    assert (page.status_code, "No books yet" in page.text) == (200, True)


def test_when_add_book_then_listed(client: fastapi.testclient.TestClient) -> None:
    _add(client)
    page = client.get("/").text
    assert ("Dune" in page, "Frank Herbert" in page, "1 book" in page) == (
        True,
        True,
        True,
    )


def test_when_add_book_without_title_then_form_shown_with_message(
    client: fastapi.testclient.TestClient,
) -> None:
    response = client.post("/books", data=_DUNE | {"title": ""})
    assert (response.status_code, "Give the book a title." in response.text) == (
        422,
        True,
    )


def test_when_add_book_then_text_escaped(
    client: fastapi.testclient.TestClient,
) -> None:
    _add(client, title="<script>alert(1)</script>")
    page = client.get("/").text
    assert ("<script>alert(1)" in page, "&lt;script&gt;alert(1)" in page) == (
        False,
        True,
    )


def test_when_record_progress_then_percentage_shown(
    client: fastapi.testclient.TestClient,
) -> None:
    book_id = _add(client)
    response = client.post(
        f"/books/{book_id}/progress",
        data={"pages_read": "103", "status": "to_read", "back": "/"},
        follow_redirects=False,
    )
    page = client.get("/").text
    assert (response.headers["location"], "103 / 412 pages · 25%" in page) == (
        f"/#book-{book_id}",
        True,
    )


def test_when_record_progress_past_end_then_row_error(
    client: fastapi.testclient.TestClient,
) -> None:
    book_id = _add(client)
    response = client.post(
        f"/books/{book_id}/progress", data={"pages_read": "500", "status": "reading"}
    )
    assert (response.status_code, "more than the book" in response.text) == (
        422,
        True,
    )


def test_when_record_progress_back_elsewhere_then_library_instead(
    client: fastapi.testclient.TestClient,
) -> None:
    book_id = _add(client)
    response = client.post(
        f"/books/{book_id}/progress",
        data={"pages_read": "1", "status": "reading", "back": "//evil.example"},
        follow_redirects=False,
    )
    assert response.headers["location"] == f"/#book-{book_id}"


def test_when_edit_book_then_saved(client: fastapi.testclient.TestClient) -> None:
    book_id = _add(client)
    form = client.get(f"/books/{book_id}")
    client.post(
        f"/books/{book_id}",
        data=_DUNE | {"title": "Dune Messiah", "rating": "4", "status": "finished"},
    )
    book = client.get("/api/books").json()[0]
    assert ('value="Dune"' in form.text, book["title"], book["pages_read"]) == (
        True,
        "Dune Messiah",
        412,
    )


def test_when_edit_book_badly_then_form_shown_with_message(
    client: fastapi.testclient.TestClient,
) -> None:
    book_id = _add(client)
    response = client.post(f"/books/{book_id}", data=_DUNE | {"rating": "9"})
    assert (response.status_code, "Rating must be from 1 to 5." in response.text) == (
        422,
        True,
    )


def test_when_delete_book_then_gone(client: fastapi.testclient.TestClient) -> None:
    book_id = _add(client)
    client.post(f"/books/{book_id}/delete")
    assert client.get("/api/books").json() == []


def test_when_missing_book_then_not_found_page(
    client: fastapi.testclient.TestClient,
) -> None:
    page = client.get("/books/99")
    assert (page.status_code, "That page isn" in page.text) == (404, True)


def test_when_search_then_only_matches_listed(
    client: fastapi.testclient.TestClient,
) -> None:
    _add(client)
    _add(client, title="Piranesi", author="Susanna Clarke")
    page = client.get("/", params={"q": "clarke", "sort": "title"}).text
    assert ("Piranesi" in page, ">Dune<" in page, "1 of 2 books" in page) == (
        True,
        False,
        True,
    )


def test_when_search_finds_nothing_then_offers_clear(
    client: fastapi.testclient.TestClient,
) -> None:
    _add(client)
    page = client.get("/", params={"q": "zzz", "status": "bogus", "sort": "bogus"})
    assert "No books match" in page.text


def test_when_api_books_filtered_then_status_applied(
    client: fastapi.testclient.TestClient,
) -> None:
    _add(client)
    _add(client, title="Piranesi", pages_read="412")
    finished = client.get("/api/books", params={"status": "finished"}).json()
    assert [(book["title"], book["progress"]) for book in finished] == [
        ("Piranesi", 1.0)
    ]


def test_when_stats_then_tiles_show_totals(
    client: fastapi.testclient.TestClient,
) -> None:
    _add(client, pages="1200", pages_read="1200", rating="4")
    _add(client, pages_read="100")
    page = client.get("/stats").text
    stats = client.get("/api/stats").json()
    assert ("1,300" in page, "Finished in 2026" in page, stats["pages_read"]) == (
        True,
        True,
        1300,
    )
    assert stats["finished_by_month"][-1] == {"count": 1, "month": "2026-11"}


def test_when_stats_empty_then_invites_first_book(
    client: fastapi.testclient.TestClient,
) -> None:
    assert "Add a book" in client.get("/stats").text


def test_when_api_missing_then_problem_details(
    client: fastapi.testclient.TestClient,
) -> None:
    response = client.post("/books/7/delete")
    api = client.get("/api/books/7")
    assert (response.status_code, api.status_code, api.json()["detail"]) == (
        404,
        404,
        "No book with id 7.",
    )


def test_when_api_book_then_one_book(client: fastapi.testclient.TestClient) -> None:
    book_id = _add(client)
    assert client.get(f"/api/books/{book_id}").json()["title"] == "Dune"


def test_when_static_requested_then_served(
    client: fastapi.testclient.TestClient,
) -> None:
    assert client.get("/static/app.css").status_code == 200


def test_when_row_saved_after_failed_add_then_library_kept(
    client: fastapi.testclient.TestClient,
) -> None:
    book_id = _add(client)
    failed = client.post("/books", data=_DUNE | {"title": ""})
    assert 'name="back" value="/"' in failed.text
    response = client.post(
        f"/books/{book_id}/progress",
        data={"pages_read": "5", "status": "reading", "back": "/"},
    )
    assert response.status_code == 200


def test_when_row_saved_during_search_then_search_kept(
    client: fastapi.testclient.TestClient,
) -> None:
    book_id = _add(client)
    page = client.get("/", params={"q": "dune"}).text
    assert 'name="back" value="/?q=dune"' in page
    response = client.post(
        f"/books/{book_id}/progress",
        data={"pages_read": "999", "status": "reading", "back": "/?q=zzz"},
    )
    assert "No books match" in response.text


def test_when_progress_without_fields_then_stored_values_kept(
    client: fastapi.testclient.TestClient,
) -> None:
    book_id = _add(client, pages_read="50")
    client.post(f"/books/{book_id}/progress", data={})
    book = client.get(f"/api/books/{book_id}").json()
    assert (book["pages_read"], book["status"]) == (50, "reading")


def test_when_huge_numbers_then_rejected_not_crashed(
    client: fastapi.testclient.TestClient,
) -> None:
    added = client.post("/books", data=_DUNE | {"pages": "99999999999999999999"})
    page = client.get("/books/99999999999999999999")
    assert (added.status_code, page.status_code) == (422, 404)


def test_when_unknown_page_then_not_found_page(
    client: fastapi.testclient.TestClient,
) -> None:
    pages = [client.get("/nope"), client.get("/books/abc")]
    assert [(page.status_code, "That page isn" in page.text) for page in pages] == [
        (404, True),
        (404, True),
    ]


def test_when_api_bad_id_then_json_errors(
    client: fastapi.testclient.TestClient,
) -> None:
    responses = [client.get("/api/books/abc"), client.get("/api/nope")]
    assert [response.status_code for response in responses] == [422, 404]
