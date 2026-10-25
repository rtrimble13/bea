# 0004. One tidy record shape for every dataset; JSON, JSONL, CSV, Parquet, table

Date: 2026-10-25
Status: accepted

## Context

`GetData` returns `Results.Data[]` rows whose columns differ by dataset: NIPA
rows have `TableName/SeriesCode/LineNumber/LineDescription/TimePeriod/...`,
Regional rows `Code/GeoFips/GeoName/TimePeriod/...`, GDPbyIndustry rows
`TableID/Frequency/Year/Quarter/Industry/...`. Values are strings with
thousands separators and markers such as `(D)`; time periods are codes
(`2024Q1`). Consumers want spreadsheets, dataframes, `jq` pipelines and data
lakes, and the same output flags as `bls`.

## Decision

Normalise every row of every dataset into a flat **record** with a fixed core
column order (`dataset, series_id, series_title, date, year, period,
frequency, value, unit, unit_mult, note_ref`), typed values (`date` as a real
date, `value` as float or null, `unit_mult` as int), chronological order, and
the dataset's own dimension columns appended in snake_case. `series_id` is
BEA's series code where the dataset has one and otherwise the dimension values
joined with `:` (ADR 0012). All formats serialise the same records:

| format | purpose |
| --- | --- |
| `json` | default for pipes; array of objects |
| `jsonl` | streaming / append-friendly |
| `csv` | spreadsheets, pandas |
| `parquet` | typed columnar storage (pyarrow, snappy) |
| `table` | humans; default on a TTY |

A `--layout wide` pivot, `--notes` (table notes as a column) and a `--raw`
escape hatch (API-shaped JSON, after filtering, without the key) are provided;
`--columns` projects identically in every format. The serialisers are the
same as in `bls`.

## Consequences

- Core column names and order are part of the contract; adding columns is a
  minor change, renaming or reordering core columns is major.
- `date` is the *first day* of the period; quarterly/annual consumers must not
  read it as a period end.
- Dimension columns vary by dataset; CSV takes the union of keys. `unit_mult`
  must be applied by the consumer (`value * 10 ** unit_mult`); values are not
  rescaled so they match what BEA publishes.
