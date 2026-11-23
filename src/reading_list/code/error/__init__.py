"""The application's own errors, raised by every layer."""

lazy import collections.abc


class AbsentError(Exception):
    """A book that was asked for does not exist."""


class InvalidError(Exception):
    """Input broke a rule; carries a message per field."""

    def __init__(self, problems: collections.abc.Mapping[str, str]) -> None:
        """Hold the problems, keyed by the field they concern.

        :param problems: A message per offending field.
        """
        super().__init__("; ".join(problems.values()))
        self.problems = dict(problems)
