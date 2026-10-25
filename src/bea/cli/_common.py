"""Shared CLI plumbing: state, output selection, error mapping, parameter parsing."""

from __future__ import annotations

import functools
import logging
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar

import httpx
import typer

from bea.client import BEAClient
from bea.config import SIGNUP_URL, Settings
from bea.errors import BEAConfigError, BEAError, ExitCode
from bea.output import OutputFormat, write_json, write_records
from bea.periods import PeriodError
from bea.records import Record, column_order

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class State:
    """Per-invocation state stored on the Typer context."""

    settings: Settings = field(default_factory=Settings.from_env)
    verbose: int = 0
    quiet: bool = False
    transport: httpx.BaseTransport | None = None  # tests inject a mock transport here


def get_state(ctx: typer.Context) -> State:
    root = ctx.find_root()
    if root.obj is None:
        root.obj = State()
    state: State = root.obj
    return state


def configure_logging(verbose: int) -> None:
    if verbose <= 0:
        return
    logging.basicConfig(
        level=logging.DEBUG, stream=sys.stderr, format="%(name)s: %(message)s", force=True
    )
    if verbose < 2:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)


def warn(state: State, message: str) -> None:
    if not state.quiet:
        sys.stderr.write(f"bea: warning: {message}\n")
        sys.stderr.flush()


def info(state: State, message: str) -> None:
    if not state.quiet:
        sys.stderr.write(f"bea: {message}\n")
        sys.stderr.flush()


def require_api_key(state: State) -> None:
    """Every live request needs a key; fail early with a clear hint when it is missing."""
    if not state.settings.has_api_key:
        raise BEAConfigError(
            "BEA_API_KEY is not set; the BEA API requires a registered UserID for every request",
            hint=f"register (free) at {SIGNUP_URL} and export BEA_API_KEY=<your 36-character key>",
        )


def build_client(state: State) -> BEAClient:
    """Create a client from the current settings (patched by tests)."""
    require_api_key(state)
    return BEAClient.from_settings(state.settings, transport=state.transport)


def resolve_format(
    state: State, fmt: OutputFormat | None, *, allow_table: bool = True
) -> OutputFormat:
    """Pick the output format: flag > BEA_FORMAT > table on a TTY, else JSON."""
    if fmt is not None:
        return fmt
    if state.settings.default_format:
        try:
            return OutputFormat(state.settings.default_format)
        except ValueError as exc:
            raise typer.BadParameter(
                f"BEA_FORMAT={state.settings.default_format!r} is not one of "
                + ", ".join(f.value for f in OutputFormat)
            ) from exc
    if allow_table and sys.stdout.isatty():
        return OutputFormat.TABLE
    return OutputFormat.JSON


def emit_records(
    state: State,
    records: Sequence[Record],
    fmt: OutputFormat,
    output: Path | None,
    *,
    columns: Sequence[str] | None = None,
    title: str | None = None,
) -> None:
    cols = list(columns) if columns else column_order(records)
    write_records(
        records,
        fmt,
        None if output is None else str(output),
        columns=cols,
        title=title,
        no_color=state.settings.no_color,
    )
    if output is not None and str(output) != "-":
        info(state, f"wrote {len(records)} row(s) to {output}")


def emit_json(state: State, obj: Any, output: Path | None) -> None:
    write_json(obj, None if output is None else str(output))
    if output is not None and str(output) != "-":
        info(state, f"wrote {output}")


def handle_errors(func: F) -> F:
    """Map package exceptions to stable exit codes and tidy stderr messages."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except BEAError as exc:
            sys.stderr.write(f"bea: error: {exc.message}\n")
            if exc.hint:
                sys.stderr.write(f"bea: hint: {exc.hint}\n")
            sys.stderr.flush()
            raise typer.Exit(code=int(exc.exit_code)) from exc
        except PeriodError as exc:
            raise typer.BadParameter(str(exc)) from exc
        except BrokenPipeError:  # e.g. `bea data ... | head`
            try:
                sys.stdout.close()
            finally:
                raise typer.Exit(code=int(ExitCode.OK)) from None

    return wrapper  # type: ignore[return-value]


def parse_params(items: Iterable[str]) -> dict[str, str]:
    """Parse ``Key=Value`` strings (repeatable) into a dict; later keys win, case-insensitively."""
    out: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise typer.BadParameter(
                f"expected PARAMETER=VALUE, got {item!r} (e.g. TableName=T10101)"
            )
        key, value = item.split("=", 1)
        key, value = key.strip(), value.strip()
        if not key:
            raise typer.BadParameter(f"empty parameter name in {item!r}")
        for existing in list(out):
            if existing.lower() == key.lower():
                del out[existing]
        out[key] = value
    return out


def parse_columns(spec: str | None) -> list[str] | None:
    if not spec:
        return None
    cols = [c.strip() for c in spec.split(",") if c.strip()]
    return cols or None


def select_columns(records: Sequence[Record], requested: Sequence[str] | None) -> list[str]:
    available = column_order(records)
    if not requested:
        return available
    missing = [c for c in requested if c not in available]
    if missing and records:
        raise typer.BadParameter(
            f"unknown column(s): {', '.join(missing)}; available: {', '.join(available)}"
        )
    return list(requested)


def values_to_records(values: Sequence[dict[str, Any]]) -> list[Record]:
    """Normalise ``GetParameterValues`` rows to ``key``/``description`` plus the raw columns.

    BEA names the columns differently per parameter (``Key``/``Desc``,
    ``TableName``/``Description``, ``FrequencyID``/``Description``, ...).
    """
    records: list[Record] = []
    for row in values:
        cols = list(row)
        key_col = next((c for c in cols if c.lower() == "key"), cols[0] if cols else None)
        desc_col = next(
            (c for c in cols if c != key_col and c.lower().endswith(("desc", "description"))),
            None,
        )
        rec: Record = {
            "key": "" if key_col is None else str(row[key_col]).strip(),
            "description": "" if desc_col is None else str(row[desc_col]).strip(),
        }
        for c in cols:
            if c not in {key_col, desc_col}:
                rec[c] = row[c]
        records.append(rec)
    return records
