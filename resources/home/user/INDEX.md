# Codex Pack Index
Purpose: route an agent to one correct runtime-pack entrypoint with minimal context load.

## Navigation
<!-- BEGIN:nav -->
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Required load order
1. `$CODEX_HOME/AGENTS.md`
2. `$CODEX_HOME/memories/MEMORY.md` when the task is repo-aware or ambiguous
3. `$CODEX_HOME/INDEX.md`
4. `$CODEX_HOME/index/pack/plans.md` and `$CODEX_HOME/index/pack/workflows.md`
5. `$CODEX_HOME/index/pack/skills.md`
6. `$CODEX_HOME/docs/style/shell-runtime.md` before shell-sensitive execution

## Fast catalogs
- Memory router: `$CODEX_HOME/memories/MEMORY.md`
- Runtime docs hub: `$CODEX_HOME/docs/OVERVIEW.md`
- Runtime workflow hub: `$CODEX_HOME/docs/workflows/overview.md`
- Runtime templates hub: `$CODEX_HOME/templates/OVERVIEW.md`
- Runtime skill roots: `$CODEX_SKILLS` and the managed admin skill root
- Plugin runtime guide: `$CODEX_HOME/docs/plugins.md`
- Multi-agent role guide: `$CODEX_HOME/MULTI_AGENT.md`

## Choose one router
- Workflow-level, cross-cutting, or unclear work -> `$CODEX_HOME/index/core/overview.md`
- Platform/tooling-specific work -> `$CODEX_HOME/index/domains/overview.md`
- Runtime-pack maintenance -> `$CODEX_HOME/index/pack/overview.md`
- Language or shell conventions only -> `$CODEX_HOME/index/style/overview.md`

## Current pack defaults
- Treat `$CODEX_HOME/index/manifest.yml` as routing metadata for pack entrypoints.
- Keep top-level routing docs short and deterministic.
- Prefer repo-aware memory routing through `$CODEX_HOME/memories/MEMORY.md`.
- Keep plugin and skill guidance anchored to installed runtime paths such as `$CODEX_HOME/plugins/cache/**`, `$CODEX_HOME/.agents/plugins/marketplace.json`, and `$CODEX_SKILLS/**`.

## High-value workflow entrypoints
- Codex installer/runtime source work -> `$CODEX_HOME/docs/workflows/codex-manager.md`
- Repo-aware memory routing -> `$CODEX_HOME/memories/MEMORY.md`
- MCP stack repo work -> `$CODEX_HOME/docs/workflows/codex-mcp.md`
- Cloudflare + GitLab delivery work -> `$CODEX_HOME/docs/workflows/cloudflare-delivery.md`
- Runtime-pack catalog maintenance -> `$CODEX_HOME/docs/workflows/runtime-pack-maintenance.md`
- Debian installer repo work -> `$CODEX_HOME/docs/workflows/debian-preseed.md`

## Stop conditions
- Open one router.
- Choose one entrypoint from that router.
- Stop broad discovery once the entrypoint is clear.

This file is aligned with `$CODEX_HOME/index/manifest.yml`.
