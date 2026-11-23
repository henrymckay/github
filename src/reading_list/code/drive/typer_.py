"""The `reading-list` command, which serves the app on this machine."""

import errno
import socket
import typing
lazy import pathlib

import platformdirs
import typer
import uvicorn

from reading_list.code.drive.fastapi_ import driver

_HOST: typing.Final = "127.0.0.1"

app = typer.Typer(add_completion=False, rich_markup_mode=None)


def _find_default_db() -> pathlib.Path:
    return platformdirs.user_data_path("reading-list").joinpath("books.db")


def _is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((_HOST, port))
        except OSError as failure:
            if failure.errno == errno.EADDRINUSE:
                return False
            raise
    return True


@app.command()
def serve(
    db: typing.Annotated[
        pathlib.Path | None,
        typer.Option(
            envvar="READING_LIST_DB",
            help="SQLite file holding the books; created if missing. "
            "[default: your user data folder]",
            show_default=False,
        ),
    ] = None,
    port: typing.Annotated[
        int, typer.Option(help="Port to serve on, on 127.0.0.1.", min=1, max=65535)
    ] = 8000,
) -> None:
    """Start the reading list and serve it at http://127.0.0.1:PORT.

    Examples:
      reading-list

      reading-list --port 8001 --db ~/books.db
    """
    path = (db or _find_default_db()).expanduser().resolve()
    if not _is_port_free(port):
        typer.echo(
            f"Port {port} is in use — try `uv run reading-list --port {port + 1}`.",
            err=True,
        )
        raise typer.Exit(code=1)
    typer.echo(
        f"Reading list running at http://{_HOST}:{port} — data in {path}\n"
        "Press Ctrl+C to stop.",
        err=True,
    )
    uvicorn.run(driver.build_app(db=path), host=_HOST, port=port, log_level="warning")
