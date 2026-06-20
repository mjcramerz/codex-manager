# Runtime-pack architecture
Purpose: explain how the codex-manager source tree, the runtime-home pack, hook runtime, and adjacent repos fit together.

## Primary surfaces
- **Installer and runtime compiler**: `src/install/**`, `config/usr/**`, `config/vendor/**`
- **Runtime-home pack source**: `resources/home/user/**`
- **Hook runtime source of truth**: `resources/hooks/scripts/lib/Codex/Hook/**`
- **Runtime skill catalog**: `resources/skills/**` plus `resources/skills/metadata.json`
- **Plugin skill catalog and marketplace**: `resources/plugins/skills/**` plus `resources/plugins/manifest.json`

## Adjacent repository map
- `/data/workspace/gitlab/computes/active/debian-preseed-di` — unattended Debian install tree, storage/profile/rendering contract
- `/data/workspace/gitlab/computes/active/cf-aptly-r2` — Cloudflare Worker front-end for Aptly content in R2
- `/data/workspace/gitlab/computes/active/cf-git-cicd-worker` — GitHub App webhook dispatcher Worker with DO/D1 controls
- `/data/workspace/gitlab/computes/active/delivery` — shared GitLab CI/CD templates for Cloudflare, salsa, and OBS flows
- `/data/workspace/gitlab/computes/active/codex-mcp` — Podman-backed MCP stack renderer/launcher
- `/var/local/virt/containerd/codex-manager` — this installer/runtime-pack source repo

## Sync boundary
- The repo is the source of truth for installable pack content.
- The runtime may preserve selected operator state back into the repo-managed home source.
- The following are runtime-only and must never sync back into `resources/home/user`:
  - `$CODEX_HOME/sessions/`
  - `$CODEX_HOME/shell_snapshots/`
  - `$CODEX_HOME/.credentials.json`

## Why the boundary matters
- Session transcripts and shell snapshots are high-churn runtime artifacts, not reusable pack guidance.
- The credential store is sensitive runtime state and must stay local to the installed environment.
- Keeping those artifacts out of the pack keeps routing fast, docs cleaner, and repo diffs reviewable.

## Source-pack operating shape
1. Route through `INDEX.md` and the `index/**` entrypoints.
2. Use `memories/MEMORY.md` only when prior decisions actually matter.
3. Update docs, plans, templates, skills, and manifest links together when entrypoints change.
4. Validate syntax and contract tests before handoff.
