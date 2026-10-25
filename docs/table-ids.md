# Datasets, tables and how to find them

The BEA API is organised in **datasets**, each with its own parameters. Most
datasets are collections of **tables** (`TableName` or `TableID`) whose rows
are **lines** (series); a few (ITA, IIP, IntlServTrade, MNE) are addressed by
indicator and dimension parameters instead. `bea` offers several routes to
the right parameters.

## 1. Offline fuzzy search: `bea search`

```bash
bea search "real gdp"
bea search "persnal income monthly"      # typos tolerated
bea search "state gdp" --dataset Regional
bea search "international" --kind all    # tables and datasets
```

Searches a curated catalog of about 75 widely used tables and indicators
(NIPA GDP, income and PCE tables; monthly personal income and PCE prices;
government, trade, saving and investment tables; fixed assets; state and
county personal income and GDP; GDP by industry; ITA balances; IIP
positions). Every hit carries a `command` column with a ready-to-run `bea
data` invocation. The catalog is deliberately small and hand-checked; it is
not the universe of BEA tables. Contributions to `src/bea/data/catalog.json`
are welcome; see [development.md](development.md#adding-a-table-to-the-curated-catalog).
[practitioners-guide.md](practitioners-guide.md) shows how these discovery
commands fit into a research workflow.

## 2. Every table of a dataset: `bea tables list`

```bash
bea tables list NIPA --query "price index"
bea tables list NIUnderlyingDetail --query "motor vehicle" --min-score 70
bea tables list Regional --limit 0 -f csv -o regional_tables.csv
bea tables list GDPbyIndustry
```

Fetches the valid `TableName`/`TableID` values from the API (cached 7 days)
and fuzzy-filters them. NIPA table ids follow the printed table numbers:
`T10101` is Table 1.1.1, `T20600` is Table 2.6, `T60200D` is Table 6.2D;
NIUnderlyingDetail ids start with `U`, FixedAssets with `FAAt`.

## 3. The lines of a table: `bea tables show`

```bash
bea tables show NIPA T10101
bea tables show GDPbyIndustry 1
bea tables show Regional SAINC1       # lists the LineCode values instead
```

Returns one row per series with its id, title, unit, available frequencies
and latest value - the fastest way to learn which `series_id` to expect in
the output or to pick a `LineCode`.

## 4. Any parameter: `bea values` and `bea datasets show`

```bash
bea datasets show Regional                         # the dataset's parameters
bea values Regional LineCode --filter TableName=SAGDP2N
bea values Regional GeoFips --query "new york"
bea values NIPA Year --filter TableName=T10101     # first/last year per frequency
bea values ITA Indicator --query "current account"
bea values GDPbyIndustry Industry --limit 0
bea values MNE DirectionOfInvestment
```

## 5. Dataset listing: `bea datasets`

```bash
bea datasets
bea datasets --query industry
bea datasets --refresh
```

## Reading the output

| Dataset | `series_id` | `series_title` | Extra columns |
| --- | --- | --- | --- |
| NIPA, NIUnderlyingDetail, FixedAssets | `SeriesCode` (`A191RL`) | `LineDescription` | `table_name`, `line_number`, `metric_name` |
| Regional | `Code:GeoFips` (`SAINC1-1:06000`) | `GeoName` | `code`, `geo_fips` |
| GDPbyIndustry, UnderlyingGDPbyIndustry | `TableID:Industry` (`1:11`) | `IndustrYDescription` | `frequency_code`, `table_id`, `industry` |
| ITA, IIP, IntlServTrade, IntlServSTA | `TimeSeriesId` | `TimeSeriesDescription` | `frequency_code`, `indicator`, `area_or_country`, ... |
| InputOutput | `TableID:RowCode:ColCode` | `RowDescr / ColDescr` | `table_id`, `row_code`, `col_code`, ... |
| MNE | `SeriesID:RowCode:ColumnCode` | `SeriesName / Row / Column` | `api_series_id`, `row_code`, `column_code`, ... |

Regional geography codes (`GeoFips`): `STATE` all states, `COUNTY` all
counties, `MSA` metropolitan areas, `00000` the United States, 2-digit state
FIPS followed by `000` (`06000` California), 5-digit county FIPS (`06037` Los
Angeles). Some Regional tables are annual (`SA*`, `CA*`, `MA*`), others
quarterly (`SQ*`).

Values carry `unit` and `unit_mult`: `value * 10 ** unit_mult` gives the
figure in units (dollars, persons, ...). Suppressed or unavailable cells
(`(D)`, `(NA)`) are `null`.

## Frequencies

NIPA and NIUnderlyingDetail tables are annual and quarterly, with a set of
monthly tables (2.6, 2.7, 2.8.x, and many underlying-detail tables);
GDPbyIndustry is annual and quarterly; ITA offers `A`, `QSA` and `QNSA`; IIP
`A` and `QNSA`; FixedAssets, InputOutput, MNE and most Regional tables are
annual. `bea values NIPA Frequency` and `bea values NIPA Year --filter
TableName=...` tell you what a table has.
