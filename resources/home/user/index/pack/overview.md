# Pack maintenance router
Purpose: choose one pack-maintenance hub for runtime-pack source work.
Use this router when maintaining the runtime pack itself: docs, plans, skills, templates, snippets, rules, config, or plugin metadata.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/index/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Required source files for pack work
- `$CODEX_HOME/index/manifest.yml` for routing metadata
- `$CODEX_HOME/memories/MEMORY.md` for repo-aware memory routing
- `$CODEX_HOME/docs/**` for runtime docs and workflows
- `$CODEX_HOME/plans/**` for plan templates
- `$CODEX_HOME/templates/**` for reusable scaffolds
- `$CODEX_SKILLS/**` for the runtime skill catalog and skill assets
- `$CODEX_HOME/plugins/cache/**` plus `$CODEX_HOME/.agents/plugins/marketplace.json` for plugin bundles and marketplace wiring

## Pack scope
- Source-managed pack content stops at docs, plans, templates, skills, rules, snippets, routing metadata, plugins, and the memory router.
- Keep installed-path references coherent across `$CODEX_HOME/**`, `$CODEX_AGENTS/**`, and `$CODEX_SKILLS/**`.
- Treat `$CODEX_HOME/memories/MEMORY.md` and the mirrored memory instruction assets as pack source when the task is memory-related.

## Choose one hub
<!-- BEGIN:contents -->
- `$CODEX_HOME/index/pack/config.md` — Pack configuration (entrypoint)
- `$CODEX_HOME/index/pack/docs.md` — Docs index (entrypoint)
- `$CODEX_HOME/index/pack/plans.md` — Plans (entrypoint)
- `$CODEX_HOME/index/pack/prompts.md` — Prompts maintenance (entrypoint)
- `$CODEX_HOME/index/pack/rules.md` — Execpolicy rules (entrypoint)
- `$CODEX_HOME/index/pack/skills.md` — Skills (entrypoint)
- `$CODEX_HOME/index/pack/snippets.md` — Snippets (entrypoint)
- `$CODEX_HOME/index/pack/style.md` — Style guides (entrypoint)
- `$CODEX_HOME/index/pack/templates.md` — Templates (entrypoint)
- `$CODEX_HOME/index/pack/workflows.md` — Workflows (entrypoint)
<!-- END:contents -->

## Recommended progression
1. Plans and workflows for execution shape
2. Skills for domain-specific playbooks
3. Shell/runtime guidance for execution safety
4. The specific pack hub you are maintaining
