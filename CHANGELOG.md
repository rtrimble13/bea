# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow
[Semantic Versioning](https://semver.org/) as `vMAJOR.MINOR.PATCH` git tags.

Releases are cut by the **Bump version** GitHub Actions workflow, which moves the
*Unreleased* section below under the new version heading.

## [Unreleased]
### Added

- `bea data` / `bea latest`: fetch observations from any BEA dataset (NIPA,
  NIUnderlyingDetail, FixedAssets, Regional, GDPbyIndustry, ITA, IIP, ...)
  with `--table` (one request per table, merged), `--frequency`, date-range
  (`--start/--end/--years`) filters, `--latest`, notes, long and wide layouts,
  and `--strict` for automations.
- Output formats: `json`, `jsonl`, `csv`, `parquet` and a rich `table`;
  `--columns` to select and order columns; `--output` to write files.
- Discovery: `bea search` (offline fuzzy search over a curated catalog of
  widely used tables and the dataset list), `bea datasets`, `bea tables list`
  / `bea tables show`, and `bea values` for any dataset parameter
  (`GetParameterValues`, cached).
- Maintenance: `bea config`, `bea doctor`, `bea cache`, `bea version`.
- Python API (`bea.BEAClient`) with retries, per-table requests and typed
  models.
- Documentation, ADRs, examples, GitHub Actions CI and tag-driven releases.
