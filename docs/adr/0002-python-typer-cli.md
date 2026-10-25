# 0002. Python package with a Typer CLI over a library core, modelled on `bls`

Date: 2026-10-25
Status: accepted

## Context

The requester already uses `bls` and wants the same experience for BEA data:
easy to install for researchers, callable from shell pipelines and agent
skills, Parquet output, identical global options and output flags. Reusing the
`bls` architecture lowers the learning curve and lets the two tools evolve
together.

## Decision

Implement `bea` as a Python 3.10+ package (`bea-cli` on PyPI, import name
`bea`) with the same structure as `bls`:

- a **library core** (`bea.client`, `bea.models`, `bea.records`, ...) that has
  no CLI concerns and is usable from notebooks and other programs;
- a **Typer** CLI (`bea.cli`) on top, one module per command group, each
  exposing `register(app)`; the same global options (`-v`, `-q`, `-V`), output
  options (`-f`, `-o`, `--columns`), panels and help conventions as `bls`;
- `httpx` for HTTP, `rapidfuzz` for fuzzy matching, `pyarrow` for Parquet,
  `rich` (via Typer) for tables;
- `src/` layout, `hatchling` build backend, `uv` for development, the same
  Makefile, CI and release workflows.

Command names follow BEA's vocabulary where `bls` used BLS's: `surveys` ->
`datasets`, `series list` -> `tables list`, `series info` -> `tables show`,
plus `values` for parameter values; `data`, `latest`, `search`, `config`,
`doctor`, `cache` and `version` are identical.

## Consequences

- Someone who knows `bls` can use `bea` immediately; scripts and skills written
  for one need only small changes for the other.
- The two code bases are intentionally similar and should be kept that way;
  improvements to shared modules (`output`, `records`, `search`, `cache`) can
  be ported across.
- The same trade-offs as `bls` apply: ~150 ms startup, ~40 MB for `pyarrow`.
