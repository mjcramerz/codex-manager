# Runtime-pack architecture
Purpose: explain how the codex-manager source tree, the runtime-home pack, hook runtime, and adjacent repos fit together.

## Primary surfaces
- **Compiled runtime configuration**: `$CODEX_HOME/config.toml`, `$CODEX_AGENTS/*.toml`, `/etc/codex/config.toml`, `/etc/codex/requirements.toml`
- **Runtime-home pack**: `$CODEX_HOME/**`
- **Hook runtime source of truth**: `$CODEX_HOME/hooks/scripts/lib/Codex/Hook/**`
- **Runtime skill catalog**: `$CODEX_SKILLS/**`
- **Plugin bundles and marketplace**: `$CODEX_HOME/plugins/cache/**` plus `$CODEX_HOME/.agents/plugins/marketplace.json`

## Adjacent repository map
- `debian-preseed-di` — unattended Debian install tree, storage/profile/rendering contract
- `cf-aptly-r2` — Cloudflare Worker front-end for Aptly content in R2
- `cf-git-cicd-worker` — GitHub App webhook dispatcher Worker with DO/D1 controls
- `delivery` — shared GitLab CI/CD templates for Cloudflare, salsa, and OBS flows
- `codex-mcp` — Podman-backed MCP stack renderer/launcher
- `codex-manager` — this installer/runtime-pack source repo

## Sync boundary
- The repo is the source of truth for installable pack content.
- Runtime state stays on the installed target and never syncs back into source control.
- Repo-managed carry-forward is limited to operator-facing state that intentionally seeds or documents the runtime:
  - `$CODEX_HOME/memories/`
  - `$CODEX_HOME/history.jsonl`
  - `$CODEX_HOME/session_index.jsonl`
  - `$CODEX_HOME/version.json`
  - `$CODEX_HOME/.personality_migration`
- The following are runtime-only and must never be treated as source-managed pack content:
  - `$CODEX_HOME/sessions/`
  - `$CODEX_HOME/shell_snapshots/`
  - `$CODEX_HOME/.credentials.json`

## Why the boundary matters
- Session transcripts and shell snapshots are high-churn runtime artifacts, not reusable pack guidance.
- The credential store is sensitive runtime state and must stay local to the installed environment.
- Keeping those artifacts out of the pack keeps routing fast, docs cleaner, and repo diffs reviewable.

## Source-pack operating shape
1. Route through `INDEX.md` and the `index/**` entrypoints.
2. Use `$CODEX_HOME/memories/MEMORY.md` when prior decisions actually matter.
3. Update docs, plans, templates, skills, and manifest links together when entrypoints change.
4. Validate syntax and contract tests before handoff.
