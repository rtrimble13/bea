# 0011. Stable exit codes; data on stdout, diagnostics on stderr

Date: 2026-10-25
Status: accepted

## Context

`bea` is called from scripts and agent skills that must decide whether to
retry, stop, or fix their command, often without a human reading the output.

## Decision

- Exit codes are an enumerated contract (`bea.errors.ExitCode`): 0 ok, 1
  unexpected, 2 usage, 3 API/HTTP failure, 4 rate limit, 5 network, 6 no data under
  `--strict`, 7 configuration. Every `BEAError` subclass carries its code; the
  CLI maps exceptions in one place (`handle_errors`).
- stdout carries only the requested data (or nothing on error). All warnings,
  API messages, progress notes and error text go to stderr, prefixed
  `bea: warning:` / `bea: error:` / `bea: hint:`. `--quiet` silences warnings,
  never errors.
- When stdout is not a terminal the default format is JSON, so a forgotten
  `--format` still yields machine-readable output.

## Consequences

- Adding an exit code is a minor change; changing the meaning of an existing
  one is major.
- Table output is never the default in pipelines, avoiding accidental parsing
  of box-drawing characters.

Inherited from `bls` (ADR 0011) with the same codes; code 4 means a
per-minute rate limit here rather than a daily quota, and code 7 also covers a
key the API rejects.
