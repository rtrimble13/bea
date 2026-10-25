# 0001. Record architecture decisions

Date: 2026-10-25
Status: accepted

## Context

`bea` is meant to be used for years by people and by automations whose authors
will not have the original design discussions available. Decisions about
output shape, exit codes and limits become contracts once scripts depend on
them. The project is a deliberate sibling of `bls`, so it also needs a record
of where it follows `bls` and where the BEA API forced a different choice.

## Decision

Keep Architecture Decision Records in `docs/adr/`, one Markdown file per
decision, in the MADR short form (context, decision, consequences), indexed in
`docs/adr/README.md`. A decision is recorded when it affects the CLI contract,
the data shape, dependencies, security or the release process. ADRs inherited
from `bls` say so explicitly.

## Consequences

- Changes to contracts must come with a new ADR (or a superseding one), which
  slows down casual breaking changes - intentionally.
- Newcomers and agents can read the "why" without digging through history, and
  people who know `bls` can see the differences at a glance.
