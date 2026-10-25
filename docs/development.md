# Development

## Setup

```bash
git clone https://github.com/rtrimble13/bea && cd bea
make install          # creates .venv with uv and installs -e ".[dev]"
source .venv/bin/activate
bea --help
```

Without `make`: `uv venv && uv pip install -e ".[dev]"`.

## Everyday commands

| Command | What it does |
| --- | --- |
| `make check` | ruff lint + format check, mypy (strict), pytest with coverage. Same as CI. |
| `make format` | ruff format + autofix |
| `make test` | pytest |
| `make build` | sdist and wheel into `dist/` |
| `pre-commit install` | optional git hooks (ruff, whitespace, yaml/json checks) |

## Layout

```
src/bea/
  cli/            Typer app: _common (plumbing), data, discover, meta
  client.py       HTTP client: API methods, retries, error mapping, per-table fetch
  config.py       Settings from environment variables
  datasets.py     Static per-dataset knowledge: parameters, series keys, titles
  periods.py      Time-period codes, frequencies, date-spec parsing, range overlap
  models.py       Observation / Series / DataResponse / Dataset / Parameter / Note
  filters.py      Client-side observation filters
  records.py      Flatten to records; wide pivot
  output.py       json / jsonl / csv / parquet / table writers
  search.py       Fuzzy scoring and search
  catalog.py      Bundled data loaders (dataset snapshot, curated tables)
  cache.py        Small file cache
  errors.py       Exceptions and exit codes
  data/           datasets.json, catalog.json
tests/            pytest suite with a fake BEA API (httpx.MockTransport)
docs/             user docs and ADRs
examples/         scripts, a GitHub Actions workflow, an agent skill
scripts/          release helpers (next_version, changelog_*)
```

## Testing philosophy

The BEA API is never called in tests. `tests/conftest.py` contains `FakeBEA`,
a small in-memory implementation of the five API methods for a few NIPA,
Regional, GDPbyIndustry and ITA tables, served through `httpx.MockTransport`.
CLI tests inject it via `State(transport=...)` passed as the Typer context
object; client tests pass it to `BEAClient(transport=...)`. The fake generates
deterministic observations (including the API's quirks: single objects
instead of one-element lists, thousands separators, `(NA)` values, `Error`
objects with HTTP 200) so tests can assert on counts, ordering and request
parameters.

To exercise the real API locally:

```bash
export BEA_API_KEY=...
bea doctor
bea latest NIPA -t T10101 -F Q -v
```

## Adding a table to the curated catalog

Edit `src/bea/data/catalog.json`. Each entry needs `id` (the table or
indicator code), `dataset`, `title`, `params` (what `bea data` must send to
fetch it, e.g. `{"TableName": "T10101"}` or `{"TableName": "SAINC1",
"LineCode": "1", "GeoFips": "STATE"}`), `frequency` (available codes,
preferred first), `units` and `tags` (search keywords). Keep headline tables
before detail tables within a dataset: ties in search score keep file order.
Verify the entry with `bea tables show DATASET TABLE` before committing.

## Supporting a new dataset

Datasets unknown to `src/bea/datasets.py` already work: parameters pass
through, and the series id is derived from every non-time dimension column. To
add shortcuts, defaults and a precise series id, add a `DatasetInfo` entry
(table parameter, frequency support, required parameters, `series_key`,
`title_columns`) and a fake table in `tests/conftest.py`.

## Style

- Python 3.10+, `from __future__ import annotations`, type hints everywhere
  (mypy strict).
- Ruff for lint and formatting, line length 100.
- CLI commands live in `src/bea/cli/*.py` and register themselves via
  `register(app)`; shared behaviour goes in `_common.py`.
- Errors raised from library code are `BEAError` subclasses; the CLI maps them
  to exit codes in `handle_errors`.
- Decisions with lasting consequences get an ADR in `docs/adr/`.
