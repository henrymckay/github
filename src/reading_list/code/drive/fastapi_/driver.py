"""Build the app: routes, static files, error pages and the guard."""

lazy import pathlib

import fastapi
import fastapi.encoders
import fastapi.exceptions
import fastapi.responses
import fastapi.staticfiles
import starlette.exceptions

from reading_list.code import error
from reading_list.code.adapt import sqlite_
from reading_list.code.drive.fastapi_ import guard, route


def _render_missing(request: fastapi.Request) -> fastapi.responses.Response:
    return route.templates.TemplateResponse(request, "missing.html", status_code=404)


def build_app(*, db: pathlib.Path) -> fastapi.FastAPI:
    """Return the app over the SQLite file at `db`.

    :param db: The SQLite file holding the books; created on first use.
    :returns: The app, ready to serve.
    """
    app = fastapi.FastAPI(
        title="Reading list",
        description="A read-only JSON view of the reading list.",
        redoc_url=None,
    )
    app.state.store = sqlite_.Store(path=db)
    app.include_router(route.router)
    app.mount(
        "/static",
        fastapi.staticfiles.StaticFiles(
            packages=[("reading_list", "data/drive/static")]
        ),
        name="static",
    )

    @app.exception_handler(error.AbsentError)
    def answer_absent(  # pyright: ignore[reportUnusedFunction]
        request: fastapi.Request, failure: error.AbsentError
    ) -> fastapi.responses.Response:
        if request.url.path.startswith("/api/"):
            return fastapi.responses.JSONResponse(
                {"title": "Not found", "status": 404, "detail": str(failure)},
                status_code=404,
                media_type="application/problem+json",
            )
        return _render_missing(request)

    @app.exception_handler(starlette.exceptions.HTTPException)
    def answer_http(  # pyright: ignore[reportUnusedFunction]
        request: fastapi.Request, failure: starlette.exceptions.HTTPException
    ) -> fastapi.responses.Response:
        if request.url.path.startswith("/api/") or failure.status_code != 404:
            return fastapi.responses.JSONResponse(
                {"detail": failure.detail},
                status_code=failure.status_code,
                headers=failure.headers,
            )
        return _render_missing(request)

    @app.exception_handler(fastapi.exceptions.RequestValidationError)
    def answer_invalid(  # pyright: ignore[reportUnusedFunction]
        request: fastapi.Request, failure: fastapi.exceptions.RequestValidationError
    ) -> fastapi.responses.Response:
        if request.url.path.startswith("/api/"):
            return fastapi.responses.JSONResponse(
                {"detail": fastapi.encoders.jsonable_encoder(failure.errors())},
                status_code=422,
            )
        return _render_missing(request)

    app.add_middleware(guard.Guard)
    return app
