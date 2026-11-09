# agent-desktop Gentoo build inputs

This is a fork of `vercel-labs/agent-desktop`. The orphan `crate-dist` default branch
contains only the producer; upstream sources remain on `main`.

Run **Create distfiles** with a stable version, or let the daily schedule select
the latest upstream release. Releases use `dist-vVERSION` on the producer branch
so GITHUB_TOKEN can publish without permission to modify upstream workflows.
Upstream version tags are not moved or reused for producer commits.

Each release includes a source archive of the exact upstream commit, a
cargo.eclass-compatible crates bundle, a license inventory, provenance and SHA256
checksums.

Existing complete releases are reused after checking their source commit, without
replacing assets. An incomplete release fails for manual inspection. No personal
token or SSH key is needed.
