# Versioning and releasing

## Scheme

Releases are git tags named `vMAJOR.MINOR.PATCH` (SemVer). The Python package
version is **derived from the tag** by `hatch-vcs` at build time; nothing in the
source tree stores the version ([ADR 0006](adr/0006-version-from-git-tags.md)).

- At tag `v1.4.0`, `bea --version` prints `bea 1.4.0`.
- Between tags, builds get a PEP 440 dev version such as `1.4.1.dev3`
  (3 commits after `v1.4.0`).
- A checkout with no tags reports `0.0.0` (or `0.1.0.devN`).

## Cutting a release (recommended: GitHub Actions)

1. Make sure `CHANGELOG.md` has the changes under `## [Unreleased]`.
2. Open **Actions -> Bump version -> Run workflow**, pick `patch`, `minor` or
   `major` (optionally `dry_run`), or run:

   ```bash
   gh workflow run bump-version.yml -f bump=minor
   ```

3. The workflow:
   - computes the next tag from the latest `v*` tag (`scripts/next_version.py`),
   - moves the *Unreleased* section under `## [X.Y.Z] - YYYY-MM-DD`
     (`scripts/changelog_release.py`), commits to `main`,
   - creates the annotated tag and pushes both,
   - calls the **Release** workflow for that tag.
4. The **Release** workflow checks out the tag, builds sdist and wheel with `uv
   build`, installs the wheel in a clean environment and asserts
   `bea version --short` equals the tag, runs the test suite against the
   installed wheel, extracts the changelog section, and creates the GitHub
   release with the artifacts attached.
5. If the repository variable `PYPI_PUBLISH` is `true`, the wheel and sdist are
   uploaded to PyPI via trusted publishing (configure the publisher on PyPI for
   this repository and the `release.yml` workflow first).

Only Linux runners are used.

## Cutting a release by hand

```bash
make release BUMP=patch        # updates CHANGELOG, commits, creates the tag locally
git push origin main vX.Y.Z    # pushing the tag triggers the Release workflow
```

Or fully manually: `git tag -a v1.2.3 -m "Release v1.2.3" && git push origin v1.2.3`.

## Rules

- Never move or delete a published tag; publish a new patch instead.
- The Release workflow fails if the built version does not match the tag, if
  the tag is not `vX.Y.Z`, or if tests fail against the built wheel.
- Breaking changes to CLI flags, output columns or exit codes bump MAJOR;
  new commands/flags/columns bump MINOR; fixes bump PATCH.
