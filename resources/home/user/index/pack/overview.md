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
- `resources/home/user/docs/**` for runtime docs
- `resources/home/user/plans/**` for plan templates
- `resources/skills/metadata.json` plus `resources/skills/**` for skill catalog and skill assets
- `resources/home/user/docs/create-prompts.md` for prompt-file catalog and rules

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
3. UNIX guide for shell-sensitive work
4. The specific pack hub you are maintaining

## Do not route here when
- the task is mainly about a consumer repository rather than the runtime pack
- a domain router already cleanly identifies the work
