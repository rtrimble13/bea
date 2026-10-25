# 0009. Linux-only GitHub Actions

Date: 2026-10-25
Status: accepted

## Context

The requester needs CI and release automation only for Linux. Cross-platform
matrices triple the runner minutes and add flakiness unrelated to the tool,
which contains no platform-specific code.

## Decision

All workflows run on `ubuntu-latest`. CI tests Python 3.10-3.13; the Release
and Bump version workflows use a single Linux job. The package itself remains
OS-independent (pure Python, `pathlib`, no shell-outs).

## Consequences

- Windows/macOS regressions would be found by users, not CI. The risk is low;
  if it materialises, add OS entries to the matrix without changing anything
  else.
- Faster, cheaper CI.

Inherited unchanged from `bls` (ADR 0009).
