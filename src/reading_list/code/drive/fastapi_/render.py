"""The Jinja environment and the formatting every screen shares."""

import typing
lazy import datetime

import fastapi
import fastapi.templating
import jinja2

from reading_list.code import transform


def format_count(value: int) -> str:
    """Return a whole number with thousands separators."""
    return f"{value:,}"


def format_day(value: datetime.date) -> str:
    """Return a date as `12 Nov 2026`."""
    return f"{value.day} {value:%b %Y}"


def format_percent(value: float) -> str:
    """Return a share from 0 to 1 as a whole percentage."""
    return f"{value:.0%}"


def _share_names(request: fastapi.Request) -> dict[str, typing.Any]:
    return {
        "Order": transform.Order,
        "Status": transform.Status,
        "path": request.url.path,
        "progress": transform.pick_progress,
    }


def build_templates() -> fastapi.templating.Jinja2Templates:
    """Return the templates, autoescaped, with the shared filters."""
    environment = jinja2.Environment(
        autoescape=True,
        loader=jinja2.PackageLoader("reading_list", "data/drive/templates"),
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=jinja2.StrictUndefined,
    )
    environment.filters["count"] = format_count
    environment.filters["day"] = format_day
    environment.filters["percent"] = format_percent
    return fastapi.templating.Jinja2Templates(
        context_processors=[_share_names], env=environment
    )
