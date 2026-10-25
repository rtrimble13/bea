"""Exception hierarchy and process exit codes.

Every error raised by this package derives from :class:`BEAError` and carries an
``exit_code`` so the CLI can map failures to stable, documented exit statuses
(see ``docs/agents.md``).
"""

from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    """Process exit codes used by the ``bea`` CLI."""

    OK = 0
    ERROR = 1  # unexpected / generic failure
    USAGE = 2  # bad arguments (also used by the argument parser)
    API = 3  # the API answered but reported a failure
    QUOTA = 4  # rate limit exceeded (requests, volume or errors per minute)
    NETWORK = 5  # transport-level problem: DNS, timeout, TLS, connection reset
    NO_DATA = 6  # --strict was given and at least one table returned nothing
    CONFIG = 7  # missing/invalid configuration (e.g. no BEA_API_KEY)


class BEAError(Exception):
    """Base class for all errors raised by the package."""

    exit_code: ExitCode = ExitCode.ERROR

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint

    def __str__(self) -> str:
        return self.message


class BEAConfigError(BEAError):
    """Configuration is missing or invalid (most often: no API key)."""

    exit_code = ExitCode.CONFIG


class BEANetworkError(BEAError):
    """The request never produced an HTTP response."""

    exit_code = ExitCode.NETWORK


class BEAHTTPError(BEAError):
    """The server answered with a non-success HTTP status or a non-JSON body."""

    exit_code = ExitCode.API

    def __init__(self, status_code: int, message: str, *, hint: str | None = None) -> None:
        super().__init__(message, hint=hint)
        self.status_code = status_code


class BEAAPIError(BEAError):
    """The API returned an ``Error`` object instead of results."""

    exit_code = ExitCode.API

    def __init__(self, code: str, description: str, *, hint: str | None = None) -> None:
        label = f"BEA API error {code}" if code else "BEA API error"
        super().__init__(f"{label}: {description or 'no detail provided'}", hint=hint)
        self.code = code
        self.description = description


class BEAQuotaError(BEAAPIError):
    """A rate limit was exceeded (BEA then blocks the key for an hour)."""

    exit_code = ExitCode.QUOTA


class BEANoDataError(BEAError):
    """Raised in ``--strict`` mode when a request returned no observations."""

    exit_code = ExitCode.NO_DATA
