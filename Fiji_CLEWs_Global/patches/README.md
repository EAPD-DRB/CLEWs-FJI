# Upstream changes

Philippines v12 retains upstream changes as patch files. The Fiji raw build
predates that convention and currently retains the complete changed files
under `../overrides/`.

The exact pinned upstream revisions are in
`../config/upstream_versions.json`, and the original change description is in
`../documentation/history/raw_build/PATCH_NOTES_2026-07-24.md`.

Before the next clean upstream rebuild, generate revision-specific patch files
here and verify that applying them reproduces the files under `overrides/`.
Until that audit is complete, `overrides/` remains authoritative and this is
an explicitly recorded reproducibility gap.
