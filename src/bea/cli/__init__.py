"""The ``bea`` command-line interface (built with Typer)."""

from __future__ import annotations

from typing import Annotated

import typer

from bea import __version__
from bea.cli import data as _data
from bea.cli import discover as _discover
from bea.cli import meta as _meta
from bea.cli._common import State, configure_logging, get_state
from bea.config import Settings

app = typer.Typer(
    name="bea",
    help=(
        "Source data from the U.S. Bureau of Economic Analysis (BEA) Data API.\n\n"
        "Set BEA_API_KEY to your 36-character UserID (free at https://apps.bea.gov/API/signup/); "
        "every live request needs it. Output defaults to a table on a terminal and JSON "
        "otherwise; use --format json|jsonl|csv|parquet|table to choose explicitly."
    ),
    no_args_is_help=True,
    rich_markup_mode="markdown",
    context_settings={"help_option_names": ["-h", "--help"]},
    pretty_exceptions_enable=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"bea {__version__}")
        raise typer.Exit()


@app.callback()
def _root(
    ctx: typer.Context,
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose", "-v", count=True, help="Log HTTP activity to stderr (-vv for wire-level)."
        ),
    ] = 0,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress warnings and notes on stderr.")
    ] = False,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = False,
) -> None:
    state: State = get_state(ctx)
    try:
        state.settings = Settings.from_env()
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    state.verbose = verbose
    state.quiet = quiet
    configure_logging(verbose)


_data.register(app)
_discover.register(app)
_meta.register(app)


def main() -> None:
    """Console-script entry point."""
    app()


__all__ = ["app", "main"]
