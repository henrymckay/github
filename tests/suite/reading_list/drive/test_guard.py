import pytest
lazy import fastapi.testclient

from reading_list.code.drive.fastapi_ import guard


@pytest.mark.parametrize(
    ("host", "method", "origin", "site", "expected"),
    argvalues=[
        ("127.0.0.1:8000", "GET", None, None, True),
        ("localhost:8000", "POST", "http://localhost:8000", "same-origin", True),
        ("[::1]", "POST", None, None, True),
        ("evil.example:8000", "GET", None, None, False),
        ("127.0.0.1:8000", "POST", "https://evil.example", None, False),
        ("127.0.0.1:8000", "POST", None, "cross-site", False),
        ("127.0.0.1:8000", "POST", None, "same-site", False),
        ("127.0.0.1:8000", "POST", "http://127.0.0.1:8000", "same-origin", True),
        ("localhost:8000", "POST", "http://localhost:3000", None, False),
    ],
)
def test_when_is_allowed_then_only_local_pages_pass(
    host: str, method: str, origin: str | None, site: str | None, expected: bool
) -> None:
    assert (
        guard.is_allowed(host=host, method=method, origin=origin, site=site) is expected
    )


def test_when_cross_site_post_then_refused(
    client: fastapi.testclient.TestClient,
) -> None:
    response = client.post(
        "/books", data={"title": "x"}, headers={"origin": "https://evil.example"}
    )
    assert response.status_code == 403
