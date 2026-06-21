# Runtime-pack maintenance workflow
Purpose: maintain the runtime-home pack, routing tree, skill catalog, templates, and repo-managed memory entrypoints without drifting into runtime-only state.

Start with `$CODEX_HOME/plans/workflows/workflow-runtime-pack-maintenance.md` before executing this workflow.

## Scope
- `$CODEX_HOME/**`
- `$CODEX_SKILLS/**`
- `$CODEX_HOME/plugins/cache/**`
- `$CODEX_HOME/.agents/plugins/marketplace.json`
- routing metadata under `$CODEX_HOME/index/manifest.yml`

## Execution flow
1) Route through the pack hubs and confirm the smallest entrypoint.
2) Audit whether the requested change affects docs, plans, templates, skills, or routing metadata.
3) Keep runtime-only artifacts out of scope (`sessions`, `shell_snapshots`, `.credentials.json`), but keep the memory router and mirrored instruction assets in scope when the task is memory-related.
4) Update cross-links, plan/workflow catalogs, and manifest links in the same change.
5) Run the narrowest contract tests for docs, skills, and manifest shape.

## Required checks
- Verify changed Markdown paths exist.
- Reparse JSON metadata after edits.
- Run the runtime-pack docs contract tests when touching routing/docs.
- Run skill/plugin contract tests when touching skill catalogs.

## Related
- `$CODEX_HOME/plans/workflows/workflow-runtime-pack-maintenance.md`
- `$CODEX_HOME/index/pack/overview.md`
- `$CODEX_HOME/docs/architecture.md`
