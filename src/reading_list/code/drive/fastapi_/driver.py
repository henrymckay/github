"""Build the app: routes, static files, error pages and the guard."""

lazy import pathlib

import fastapi
import fastapi.responses
import fastapi.staticfiles

from reading_list.code import error
from reading_list.code.adapt import sqlite_
from reading_list.code.drive.fastapi_ import guard, route


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
        return route.templates.TemplateResponse(
            request, "missing.html", {"detail": str(failure)}, status_code=404
        )

    app.add_middleware(guard.Guard)
    return app
