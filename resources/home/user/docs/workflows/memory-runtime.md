# Memory runtime workflow (retired)

Purpose: record that the standalone memory-runtime transfer workflow was removed from this repo.


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
- If the task is about runtime-home synchronization, installer-owned memory files, or stale memory documentation, use `$CODEX_HOME/docs/workflows/codex-repo.md`.
- If the task is about repo hygiene while removing old memory-runtime references, use `$CODEX_HOME/docs/workflows/repo-ops.md`.
- Verify any related change with the narrowest runtime checks available for the active Codex installation.

## Cleanup checklist
1. Remove or rewrite stale references to `codex-db-fetch`.
2. Remove or rewrite stale references to `$CODEX_ROOT/mem/export` and `$CODEX_ROOT/mem/import`.
3. Route replacement guidance through `codex-repo.md` or `repo-ops.md` instead of recreating the retired workflow.

## Security checkpoints
- Treat any request to revive the removed memory-transfer flow as a behavior change that needs explicit approval.
- Keep runtime memory artifacts out of git history unless the user explicitly requests a sanitized snapshot.

## Testing checkpoints
- Search for stale references in touched files before handoff.
- Run the narrowest relevant validation commands after related documentation updates.

## Deployment checkpoints
- Land documentation cleanup before telling operators to use memory-related guidance.
- Record any removed legacy references in the final handoff note.

## Multi-agent handoff
- Explorers inventory stale references only.
- One owner removes or rewrites the legacy guidance and reports the replacement entrypoint.

See also:
- `$CODEX_HOME/docs/workflows/codex-repo.md`
- `$CODEX_HOME/docs/workflows/repo-ops.md`
- `$CODEX_HOME/index/core/codex-repo.md`
- `$CODEX_HOME/index/core/repo-ops.md`
