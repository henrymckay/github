"""The values routes depend on, overridable in tests."""

import datetime

lazy import fastapi

lazy from reading_list.code import port


def read_today() -> datetime.date:
    """Return today's date on this machine, the day a person sees."""
    return datetime.date.today()


def store(request: fastapi.Request) -> port.Store:
    """Return the store the app was built with."""
    built: port.Store = request.app.state.store
    return built
