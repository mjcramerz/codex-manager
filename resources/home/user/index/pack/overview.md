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
- `resources/home/user/index/manifest.yml` for routing metadata
- `resources/home/user/docs/**` for runtime docs and workflows
- `resources/home/user/plans/**` for plan templates
- `resources/home/user/templates/**` for reusable scaffolds
- `resources/skills/metadata.json` plus `resources/skills/**` for runtime skill catalog and skill assets
- `resources/plugins/skills/**` plus `resources/plugins/manifest.json` for plugin skills and marketplace wiring

## Runtime-state boundary
- Source-managed pack content stops at docs, plans, templates, skills, rules, snippets, and routing metadata.
- Do not reintroduce runtime-only sync for sessions, shell snapshots, or credential store files.
- Treat `$CODEX_HOME/memories/` as runtime state even when docs mention it as an optional repo-aware input.

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
