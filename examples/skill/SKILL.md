---
name: bea-data
description: Fetch U.S. national, regional and international economic accounts (GDP, personal income, PCE prices, GDP by industry, state and county data, trade balances) from the Bureau of Economic Analysis with the `bea` CLI. Use when a task needs official BEA tables, the latest reading of GDP or income, or a CSV/Parquet extract of BEA data.
---

# BEA data via the `bea` CLI

`bea` is a command-line client for the BEA Data API. It is installed
(`bea --version` works) and reads the API key from `BEA_API_KEY`; every live
request needs that key (exit 7 without it).

## Rules

1. Always pass `--format json` (or `jsonl`/`csv`/`parquet` for files). Parse
   **stdout** only; stderr holds warnings.
2. Resolve the table and parameters before fetching data:
   - `bea search "<plain words>" --limit 5 --format json` (offline, free).
     Each hit has a `command` field; use the top hit if its `score` >= 90,
     otherwise show the user the candidates.
   - For something not in the curated catalog:
     `bea tables list <DATASET> --query "<words>" --limit 10 --format json`
     (`NIPA` national accounts, `NIUnderlyingDetail` detailed NIPA,
     `Regional` states/counties/metros, `GDPbyIndustry`, `ITA` international
     transactions, `IIP` investment position, `FixedAssets`). Run
     `bea datasets --format json` for the full list and
     `bea datasets show <DATASET> --format json` for its parameters.
   - To learn a table's lines (series ids and titles):
     `bea tables show <DATASET> <TABLE> --format json`. For Regional line codes
     and geographies: `bea values Regional LineCode --filter TableName=<T>` and
     `bea values Regional GeoFips --query "<state>"`.
3. Fetch with one call per table set:
   - latest: `bea latest NIPA -t T10101 -F Q --format json --strict`
   - range: `bea data NIPA -t T10101 -F Q --start YYYY-Qn --end YYYY-Qn --format json`
   - regional: `bea data Regional -t SAINC1 --line 1 --geo STATE --years 5 --format json`
   - other datasets: pass parameters as `NAME=VALUE`, e.g.
     `bea data ITA Indicator=BalGds AreaOrCountry=AllCountries -F QSA --years 3`
   - notes/footnotes: add `--notes`
4. Interpret exit codes: `0` ok; `2` your flags or parameters were wrong (read
   stderr, it names the missing parameter); `3` bad table/parameter or API
   error; `4` rate limit (stop for an hour, tell the user); `5` network (retry
   once after a pause); `6` no data; `7` key missing or rejected.
5. Budget: 100 requests, 100 MB and 30 errors per minute per key; exceeding
   any blocks the key for an hour. Do not loop over tables or years one at a
   time, and do not guess parameters repeatedly - use the discovery commands.

## Output schema

Each JSON row: `dataset, series_id, series_title, date (YYYY-MM-DD, first day
of period), year, period (2024 | 2024Q1 | 2024M01), frequency (annual |
quarterly | monthly), value (number or null), unit, unit_mult (power of ten:
6 = millions), note_ref`, plus the dataset's dimension columns
(`table_name`, `line_number`, `geo_fips`, `industry`, ...). Report values with
their `unit`; multiply by `10 ** unit_mult` only when the user wants raw
units.

## Worked example

User: "How fast did the U.S. economy grow last quarter, and what did consumer
spending do?"

```bash
bea search "real gdp growth" --limit 3 --format json     # -> T10101 (NIPA), command included
bea latest NIPA -t T10101 -F Q --format json             # rows for every line of the table
```

Report `period`, `value` and `unit` for `series_id` `A191RL` (Gross domestic
product) and `DPCERL` (Personal consumption expenditures). Quarterly NIPA
growth rates are seasonally adjusted annual rates.

## Reference

For anything beyond a single lookup (growth versus levels, contributions,
PCE inflation arithmetic, state rankings, revisions and release lags, the
answer template), follow
[`docs/practitioners-guide.md`](../../docs/practitioners-guide.md), especially
section 7 (agent protocol) and section 8 (question playbook).
