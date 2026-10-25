# bea

[![CI](https://github.com/rtrimble13/bea/actions/workflows/ci.yml/badge.svg)](https://github.com/rtrimble13/bea/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

A command-line client (and small Python library) for the
[U.S. Bureau of Economic Analysis Data API](https://apps.bea.gov/API/signup/):
GDP and its components (NIPA), personal income, PCE prices, GDP by industry,
state and county data (Regional), international transactions and more. It is
the sibling of [`bls`](https://github.com/rtrimble13/bls) and shares its
design: one tool for people doing ad-hoc research in a terminal and for
automations or AI agents that need predictable, scriptable access to official
time series.

```console
$ export BEA_API_KEY=...            # free 36-character UserID from https://apps.bea.gov/API/signup/
$ bea data NIPA --table T10101 --frequency Q --start 2024-Q1 --end 2024-Q3 --format csv --columns series_id,series_title,period,value
series_id,series_title,period,value
A191RL,Gross domestic product,2024Q1,1.6
A191RL,Gross domestic product,2024Q2,3.0
A191RL,Gross domestic product,2024Q3,3.1
DPCERL,Personal consumption expenditures,2024Q1,1.9
DPCERL,Personal consumption expenditures,2024Q2,2.8
DPCERL,Personal consumption expenditures,2024Q3,3.7
...
```

## Features

- **Every dataset the API offers**: `bea data DATASET` wraps `GetData` for
  NIPA, NIUnderlyingDetail, FixedAssets, Regional, GDPbyIndustry,
  UnderlyingGDPbyIndustry, ITA, IIP, InputOutput, IntlServTrade, IntlServSTA
  and MNE, with shortcuts (`--table`, `--frequency`, `--geo`, `--line`,
  `--industry`) and `NAME=VALUE` pass-through for everything else.
- **Normalised records**: every dataset's rows become the same tidy shape
  (`series_id`, `series_title`, `date`, `year`, `period`, `frequency`,
  `value`, `unit`, `unit_mult`, ...) with the dataset's own dimensions as
  extra columns; `TimePeriod` codes such as `2024Q1` become real dates.
- **Filters the API lacks**: inclusive date ranges down to the month
  (`--start 2020-03 --end 2024-Q2`), `--years N`, `--latest`, several tables in
  one call (one request each, merged); transient failures are retried with
  back-off.
- **Output for humans and machines**: `table`, `json`, `jsonl`, `csv`,
  `parquet`; long (tidy) or wide layouts; `--columns` to pick columns;
  `--notes` to attach the table notes; `--raw` for the untouched API shape.
- **Discovery with fuzzy search**: `bea search "real gdp"` works offline
  against a curated catalog of ~75 widely used tables and indicators and
  prints a ready-to-run command for each hit; `bea tables list NIPA --query
  pce`, `bea tables show NIPA T10101` and `bea values Regional GeoFips` use
  the live metadata methods (cached).
- **Automation friendly**: API key from the environment only, stable exit
  codes, warnings on stderr and data on stdout, `--strict`, `--quiet`, JSON by
  default when piped.
- **Linux CI, tag-driven releases**: versions are derived from `vX.Y.Z` git
  tags; a one-click workflow bumps, tags and publishes.

## Installation

Requires Python 3.10+.

```bash
# with uv (recommended)
uv tool install git+https://github.com/rtrimble13/bea
# or with pipx
pipx install git+https://github.com/rtrimble13/bea
# or into the current environment
pip install git+https://github.com/rtrimble13/bea
```

For development:

```bash
git clone https://github.com/rtrimble13/bea && cd bea
make install        # uv venv + editable install with dev extras
make check          # ruff, mypy, pytest
```

## Configuration

Set your key once; everything else has sensible defaults.

| Variable | Purpose | Default |
| --- | --- | --- |
| `BEA_API_KEY` | Your 36-character UserID. **Required for every live request**; BEA has no anonymous access. | unset |
| `BEA_FORMAT` | Default `--format` (`json`, `jsonl`, `csv`, `parquet`, `table`). | `table` on a TTY, `json` otherwise |
| `BEA_CACHE_DIR` | Where the dataset list, parameter lists and parameter values are cached. | `$XDG_CACHE_HOME/bea` or `~/.cache/bea` |
| `BEA_TIMEOUT` | HTTP timeout in seconds. | `60` |
| `BEA_MAX_RETRIES` | Retries for 429/5xx/network errors. | `3` |
| `BEA_USER_AGENT` | User-Agent header. | `bea-cli/<version> (+repo url)` |
| `BEA_API_BASE_URL` | Override the API endpoint (testing, proxies). | `https://apps.bea.gov/api/data` |
| `NO_COLOR` | Disable colour in table output. | unset |

The key is deliberately **not** accepted as a flag (see
[ADR 0003](docs/adr/0003-api-key-from-environment.md)). `bea config` prints the
effective configuration with the key masked; `bea doctor` additionally checks
connectivity.

## Usage

```text
bea data      Fetch observations from a dataset (GetData)
bea latest    Newest observation per series (alias for data --latest)
bea search    Fuzzy-search the curated table catalog and the dataset list (offline)
bea datasets  List datasets; `datasets show NIPA` for its parameters
bea tables    list DATASET [--query] (every table) | show DATASET TABLE (its lines)
bea values    DATASET PARAMETER [--filter K=V] (valid parameter values)
bea config    Effective configuration (key masked)
bea doctor    Configuration + connectivity check
bea cache     info | clear
bea version   Print the version
```

Run `bea <command> --help` for all options. Highlights:

```bash
# Real GDP growth, quarterly, 2019 through Q2 2024, one column per line of the table
bea data NIPA --table T10101 --frequency Q --start 2019 --end 2024-Q2 --layout wide -f csv -o gdp.csv

# Monthly PCE price indexes for the last 2 years, as Parquet
bea data NIPA -t T20804 -F M --years 2 -f parquet -o pce_prices.parquet

# Personal income by state (table SAINC1, line 1), latest value per state
bea latest Regional --table SAINC1 --line 1 --geo STATE

# Value added by industry, annual, two industries, with the table notes attached
bea data GDPbyIndustry -t 1 -F A --industry 11 --industry 21 --years 5 --notes

# Balance on goods, quarterly seasonally adjusted (any parameter as NAME=VALUE)
bea data ITA Indicator=BalGds AreaOrCountry=AllCountries -F QSA --years 3

# Everything a table has (Year=ALL maps to the dataset's "all years" value)
bea data NIPA -t T10105 -F A Year=ALL -f jsonl

# Find tables without knowing their ids
bea search "real gdp growth"              # offline; prints a ready-to-run command per hit
bea search "personal income" --kind all   # tables and datasets
bea tables list NIPA --query "price index"   # every NIPA table, live metadata (cached)
bea tables show NIPA T10101               # the lines of a table and their latest value
bea values Regional LineCode --filter TableName=SAINC1
bea values Regional GeoFips --query california

# Exactly what the API returned (after client-side filtering, UserID removed)
bea data NIPA -t T10101 -F Q --latest --raw
```

### Datasets and parameters

Each dataset has its own required parameters; `bea datasets show DATASET`
lists them. The shortcuts map to parameters as follows:

| Flag | Parameter | Datasets |
| --- | --- | --- |
| `-t, --table` | `TableName` | NIPA, NIUnderlyingDetail, FixedAssets, Regional |
| `-t, --table` | `TableID` | GDPbyIndustry, UnderlyingGDPbyIndustry, InputOutput |
| `-F, --frequency` | `Frequency` (`A`, `Q`, `M`; ITA/IIP also `QSA`/`QNSA`) | NIPA, NIUnderlyingDetail, GDPbyIndustry, UnderlyingGDPbyIndustry, ITA, IIP |
| `-g, --geo` | `GeoFips` | Regional |
| `-l, --line` | `LineCode` | Regional |
| `-i, --industry` | `Industry` (default `ALL`) | GDPbyIndustry, UnderlyingGDPbyIndustry |
| `NAME=VALUE` / `-p` | anything | all |

### Dates and frequencies

`--start`/`--end` accept `YYYY`, `YYYY-MM`, `YYYY-MM-DD`, `YYYY-Qn`, `YYYY-Hn`
and BEA's own `YYYYQn`/`YYYYMnn`. Both bounds are inclusive. The API only
understands whole years (`Year=2023,2024`), so the CLI requests the covering
years and trims locally; a period is kept when **any part of it overlaps** the
range, so `--start 2020-06` keeps Q2 2020 and the 2020 annual value
([ADR 0007](docs/adr/0007-client-side-filtering.md)). Without a date flag the
last three calendar years are requested; `Year=ALL` (or `X`) asks for
everything.

BEA time periods map to frequencies as follows: `2024` annual, `2024Q1`
quarterly, `2024M01` monthly. Datasets that report `Year`/`Quarter` columns
instead (GDPbyIndustry, InputOutput, MNE) are normalised to the same codes.

### Output

Long layout columns, always in this order:

```
dataset, series_id, series_title, date, year, period, frequency, value, unit, unit_mult, note_ref
```

followed by `notes` (with `--notes`) and the dataset's own dimension columns in
snake_case (`table_name`, `line_number`, `metric_name` for NIPA; `code`,
`geo_fips` for Regional; `table_id`, `industry` for GDPbyIndustry; ...).
`series_id` is BEA's series code where one exists (`A191RL`,
`BalGds_AllCountries_A`) and otherwise a `:`-joined key of the dimension
columns (`SAINC1-1:06000`, `1:11`). `date` is the first day of the period;
`value` is a float, `null` when BEA reports `(D)`, `(NA)` or similar;
`unit_mult` is the power of ten the value is expressed in (`6` = millions).

The wide layout has one row per period and one column per series id. See
[docs/output-formats.md](docs/output-formats.md) for schemas and examples.

### Exit codes

| Code | Meaning |
| --- | --- |
| 0 | success |
| 1 | unexpected error |
| 2 | usage error (bad flag, bad date, missing required parameter, unknown column) |
| 3 | the API reported an error or returned an HTTP error |
| 4 | rate limit exceeded (100 requests / 100 MB / 30 errors per minute; one-hour block) |
| 5 | network problem (DNS, timeout, connection reset) |
| 6 | `--strict` and a request returned no observations |
| 7 | configuration error (no or rejected `BEA_API_KEY`) |

Warnings (empty tables, split requests) go to **stderr**; data goes to
**stdout**. `--quiet` silences the warnings.

## Python API

```python
from bea import BEAClient, Settings

with BEAClient.from_settings(Settings.from_env()) as client:  # or BEAClient(api_key="...")
    resp = client.fetch(
        "NIPA", {"Frequency": "Q", "Year": "2023,2024"}, table_param="TableName", tables=["T10101"]
    )
    for series in resp.series:
        for obs in series.data:
            print(series.series_id, series.title, obs.date, obs.value)
```

See [docs/python-api.md](docs/python-api.md).

## For agents and automations

`bea` is designed to be called from scripts, cron jobs, GitHub Actions and
agent skills. [docs/agents.md](docs/agents.md) is a compact contract
(commands, flags, output schema, exit codes, rate-limit guidance) that a skill
can reference, and [examples/skill/SKILL.md](examples/skill/SKILL.md) is a
ready-made skill. [examples/github-actions/](examples/github-actions/)
contains a scheduled data-pull workflow.

## Documentation

- [docs/usage.md](docs/usage.md) - full command reference
- [docs/configuration.md](docs/configuration.md) - environment variables, limits, caching
- [docs/output-formats.md](docs/output-formats.md) - record schema per format
- [docs/table-ids.md](docs/table-ids.md) - datasets, tables and how to find them
- [docs/agents.md](docs/agents.md) - the contract for agentic workflows
- [docs/python-api.md](docs/python-api.md) - using the library
- [docs/development.md](docs/development.md) - contributing, tests, tooling
- [docs/releasing.md](docs/releasing.md) - versioning and the release workflow
- [docs/adr/](docs/adr/) - architecture decision records
- [CHANGELOG.md](CHANGELOG.md)

## Versioning

Versions are `vMAJOR.MINOR.PATCH` git tags; the package version is derived from
them at build time (hatch-vcs). Releases are produced by the **Bump version**
workflow in the Actions tab (choose patch/minor/major), which updates
`CHANGELOG.md`, tags, builds, verifies, and publishes a GitHub release
([docs/releasing.md](docs/releasing.md)).

## Data notes

- BEA data are public domain; see the
  [BEA API terms of service](https://apps.bea.gov/API/_pdf/BEA_API_Terms_of_Service.pdf)
  and the [API user guide](https://apps.bea.gov/API/docs/index.htm).
- The API limits each key to 100 requests, 100 MB and 30 errors per minute and
  blocks keys that exceed this for one hour; `bea` exits with code 4 when that
  happens.
- The bundled dataset list is a snapshot; `bea datasets --refresh` fetches the
  live list and caches it.

## License

MIT - see [LICENSE](LICENSE).
