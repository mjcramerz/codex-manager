# Memory router
Purpose: route memory-related work to one maintained entrypoint without confusing source-managed memory assets with runtime-only state.

## Navigation
<!-- BEGIN:nav -->
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Use this file when
- the task is repo-aware, ambiguous, or depends on prior decisions
- you are updating memory instruction assets or memory configuration
- you need to clean up stale memory-transfer guidance without recreating retired flows

## Route to one maintained entrypoint
- Memory config and install/render behavior -> `$CODEX_HOME/docs/workflows/codex-manager.md`
- Memory workflow cleanup and retired transfer guidance -> `$CODEX_HOME/docs/workflows/memory-runtime.md`
- Runtime-pack docs, plans, and routing changes -> `$CODEX_HOME/docs/workflows/runtime-pack-maintenance.md`

## Source-managed memory assets
- Memory instruction sources: `$CODEX_HOME/instructions/memories/`
- Mirrored disable-path assets: `$CODEX_HOME/.models/instructions/memories/`
- Runtime memory configuration is rendered into `$CODEX_HOME/config.toml`

## Boundary rules
- Treat `$CODEX_HOME/memories/` in this pack as operator-facing source content only when the task is about the memory router, seeded carry-forward docs, or memory instruction assets.
- Treat `$CODEX_HOME/sessions/`, `$CODEX_HOME/shell_snapshots/`, and `$CODEX_HOME/.credentials.json` as runtime-only artifacts.
- Do not recreate retired export/import workflows or runtime dumps as source-managed pack guidance.
