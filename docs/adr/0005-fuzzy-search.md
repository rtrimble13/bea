# 0005. Offline fuzzy search over a curated table catalog with RapidFuzz

Date: 2026-10-25
Status: accepted

## Context

The API cannot search; users must know that real GDP growth is NIPA table
`T10101` and state personal income is Regional `SAINC1` line 1. Agents in
particular need to turn "pce inflation" into a runnable command without
spending requests, and every request against a wrong guess counts towards the
30-errors-per-minute block.

## Decision

Three layers, mirroring `bls` (ADR 0005):

1. **`bea search`** - offline fuzzy search over a *curated* JSON catalog of
   ~75 headline tables and indicators (id, dataset, title, the parameters that
   fetch it, frequencies, units, tags) plus the dataset list. The scorer is the
   same per-token scheme as `bls` (exact tag 1.0, whole word 0.95, substring
   0.75, RapidFuzz ratio >= 72 at 0.8 x ratio; exact id/tag/title = 100), ties
   keep catalog order. Each hit carries a ready-to-run `command`.
2. **`bea tables list DATASET --query ...`** and **`bea values DATASET
   PARAMETER --query ...`** - exhaustive search over the API's own metadata
   (ADR 0010).
3. **`bea tables show`** - live description of a table's lines.

## Consequences

- The curated catalog must be maintained by hand; wrong ids are the main risk,
  so contributors verify with `bea tables show`.
- Search results are deterministic and explainable (score bands), which suits
  agents.
- Not every BEA table is discoverable offline; the docs make the three layers
  explicit.
