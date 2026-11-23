"""Refuse requests that did not come from this machine's own pages."""

import typing
import urllib.parse

import starlette.responses
import starlette.types

_HOSTS: typing.Final = frozenset({"127.0.0.1", "localhost", "[::1]"})
_SAFE: typing.Final = frozenset({"GET", "HEAD", "OPTIONS"})
_SAME_SITE: typing.Final = frozenset({"same-origin", "none"})


def _host_name(host: str) -> str:
    return host.rsplit(":", 1)[0] if not host.endswith("]") else host


def is_allowed(*, host: str, method: str, origin: str | None, site: str | None) -> bool:
    """Return whether a request may reach the app.

    A loopback Host stops a DNS-rebound name; a write must come from this
    very origin, port included, so no other site, even one on another local
    port, can post to the app.

    :param host: The Host header.
    :param method: The HTTP method.
    :param origin: The Origin header, if sent.
    :param site: The Sec-Fetch-Site header, if sent.
    :returns: True if the request may go on.
    """
    if _host_name(host) not in _HOSTS:
        return False
    if method in _SAFE:
        return True
    if site is not None and site not in _SAME_SITE:
        return False
    if origin is None:
        return True
    return urllib.parse.urlsplit(origin).netloc == host


class Guard:
    """ASGI middleware applying `is_allowed` to every HTTP request."""

    def __init__(self, app: starlette.types.ASGIApp) -> None:
        """Wrap the app.

        :param app: The app to guard.
        """
        self.app = app

    async def __call__(
        self,
        scope: starlette.types.Scope,
        receive: starlette.types.Receive,
        send: starlette.types.Send,
    ) -> None:
        """Answer 403 to a refused request, else pass it on."""
        if scope["type"] == "http":
            headers = {
                key.decode("latin-1"): value.decode("latin-1")
                for key, value in scope["headers"]
            }
            if not is_allowed(
                host=headers.get("host", ""),
                method=scope["method"],
                origin=headers.get("origin"),
                site=headers.get("sec-fetch-site"),
            ):
                response = starlette.responses.PlainTextResponse(
                    "Refused: the reading list only answers its own pages "
                    "on this machine.",
                    status_code=403,
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
