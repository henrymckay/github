import socket
lazy import pathlib

import typer.testing
import uvicorn
lazy import pytest

from reading_list.code.drive import cli


def test_when_port_taken_then_exit_1_with_advice() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as held:
        held.bind(("127.0.0.1", 0))
        held.listen()
        port = held.getsockname()[1]
        result = typer.testing.CliRunner().invoke(cli.app, ["--port", str(port)])
    assert (result.exit_code, f"--port {port + 1}" in result.output) == (1, True)


def test_when_bad_port_then_usage_error() -> None:
    result = typer.testing.CliRunner().invoke(cli.app, ["--port", "0"])
    assert result.exit_code == 2


def test_when_serve_then_uvicorn_runs_on_loopback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    calls: list[tuple[str, int]] = []

    def fake_run(app: object, *, host: str, port: int, log_level: str) -> None:
        calls.append((host, port))

    monkeypatch.setattr(uvicorn, "run", fake_run)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        free = probe.getsockname()[1]
    result = typer.testing.CliRunner().invoke(
        cli.app, ["--port", str(free), "--db", str(tmp_path / "b.db")]
    )
    assert (result.exit_code, calls, "Reading list running at" in result.output) == (
        0,
        [("127.0.0.1", free)],
        True,
    )


def test_when_port_left_in_time_wait_then_still_free() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", 0))
        server.listen()
        port = server.getsockname()[1]
        with socket.create_connection(("127.0.0.1", port)):
            accepted, _ = server.accept()
            accepted.close()
    assert cli_port_is_free(port)


def cli_port_is_free(port: int) -> bool:
    from reading_list.code.drive import typer_

    return typer_._is_port_free(port)  # pyright: ignore[reportPrivateUsage]
