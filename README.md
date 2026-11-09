# agent-desktop Gentoo build inputs

This is a fork of `vercel-labs/agent-desktop`. The orphan `crate-dist` branch contains
only this producer; upstream sources remain on `main` and the upstream version tags.

Run **Create distfiles** with a stable version, or let the daily schedule select
the latest upstream release. The release tag `vVERSION` points to the upstream
commit, not to this CI branch. Releases contain a cargo.eclass-compatible crates
bundle, a license inventory, provenance and SHA256 checksums.

Existing complete releases are reused without replacing assets. An incomplete
release fails for manual inspection instead of changing already published bytes.
The producer uses the repository GITHUB_TOKEN and needs no personal token or SSH key.
