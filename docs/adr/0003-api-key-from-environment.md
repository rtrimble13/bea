# 0003. API key only from the environment; no anonymous mode

Date: 2026-10-25
Status: accepted

## Context

BEA issues a free 36-character *UserID* and requires it on every request;
there is no anonymous tier (unlike BLS). Keys are rate limited per key and a
key that misbehaves is blocked for an hour. The tool runs in shells, cron, CI
and agent sandboxes, where a `--api-key` flag would leak into history, process
listings and transcripts.

## Decision

Read the key exclusively from `BEA_API_KEY` (inherited from `bls`, ADR 0003).
Provide no flag and no config file. Because the API has no anonymous mode,
every live command fails *before* making a request when the key is unset,
with exit code 7 and a hint pointing at the sign-up page. When the API rejects
the key, that error is also mapped to exit code 7 so scripts can tell "fix the
key" from "fix the request". `bea config` and `bea doctor` print the key
masked; `doctor` additionally checks the key has the expected length. The key
is sent only as the `UserID` query parameter, never logged, and stripped from
`--raw` output.

## Consequences

- Secrets management is delegated to the environment, where it belongs.
- Offline commands (`search`, `datasets` without `--refresh`, `config`,
  `cache`, `version`) work without a key; everything else needs one.
- Tests never need a real key: the fake API accepts a test key, and the client
  can be constructed with `api_key=None`.
