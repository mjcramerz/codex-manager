# Memory runtime workflow (retired)
Purpose: record that the standalone memory-transfer workflow was removed from this repo and route current memory work to the maintained entrypoints.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/workflows/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Status
- The legacy `codex-db-fetch` export/import flow no longer exists.
- The legacy `$CODEX_ROOT/mem/export` and `$CODEX_ROOT/mem/import` staging paths no longer exist.
- Do not add new guidance, tests, or automation around those removed commands or paths.

## Current guidance
- For repo-aware memory context, use `$CODEX_HOME/memories/MEMORY.md`.
- For memory instruction-source changes, update both `$CODEX_USER_DIR/instructions/memories/` and `$CODEX_HOME/.models/instructions/memories/` together and keep the rendered `$CODEX_HOME/config.toml` memory overrides aligned.
- For installer-owned memory/state handling, use `$CODEX_HOME/docs/workflows/codex-manager.md`.
- For runtime-pack cleanup or catalog updates, use `$CODEX_HOME/docs/workflows/runtime-pack-maintenance.md`.

## Current boundary
- The retired transfer flow is not replaced by ad hoc state copies or alternate staging paths.
- Route all current memory guidance through the maintained entrypoints listed above.

## Cleanup checklist
1. Remove or rewrite stale references to `codex-db-fetch`.
2. Remove or rewrite stale references to `$CODEX_ROOT/mem/export` and `$CODEX_ROOT/mem/import`.
3. Route replacement guidance through the memory router, `codex-manager.md`, or `runtime-pack-maintenance.md` instead of recreating the retired workflow.

## Testing checkpoints
- Search for stale references in touched files before handoff.
- Run the narrowest relevant validation commands after related documentation updates.

See also:
- `$CODEX_HOME/memories/MEMORY.md`
- `$CODEX_HOME/docs/workflows/codex-manager.md`
- `$CODEX_HOME/docs/workflows/runtime-pack-maintenance.md`
- `$CODEX_HOME/index/core/codex-repo.md`
