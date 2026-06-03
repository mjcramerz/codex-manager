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
6. `$CODEX_HOME/UNIX.md` before shell-sensitive execution

## Fast catalogs
- Runtime docs hub: `$CODEX_HOME/docs/OVERVIEW.md`
- Runtime prompt guide: `$CODEX_HOME/docs/create-prompts.md`
- Runtime snippets hub: `$CODEX_HOME/snippets/OVERVIEW.md`
- Runtime templates hub: `$CODEX_HOME/templates/OVERVIEW.md`
- Runtime skill roots: `$CODEX_SKILLS` and the managed admin skill root
- Plugin runtime guide: `$CODEX_HOME/docs/plugins.md`
- Multi-agent role guide: `$CODEX_HOME/MULTI_AGENT.md`

## Choose one router
- Workflow-level, cross-cutting, or unclear work -> `$CODEX_HOME/index/core/overview.md`
- Platform/tooling-specific work -> `$CODEX_HOME/index/domains/overview.md`
- Runtime-pack maintenance -> `$CODEX_HOME/index/pack/overview.md`
- Language or shell conventions only -> `$CODEX_HOME/index/style/overview.md`

## Pack maintenance defaults
- Treat `resources/home/user/index/manifest.yml` as routing metadata for pack entrypoints.
- Keep top-level routing docs short and deterministic.
- When canonical paths or related-link contracts change, update the affected entrypoint and manifest in the same change.

## Router catalog
- `$CODEX_HOME/index/core/overview.md` — core workflows and execution guardrails
- `$CODEX_HOME/index/domains/overview.md` — platform and tooling routers
- `$CODEX_HOME/index/pack/overview.md` — docs, plans, skills, templates, snippets, rules, and config
- `$CODEX_HOME/index/style/overview.md` — style guides and shell/language conventions

## Stop conditions
- Open one router.
- Choose one entrypoint from that router.
- Stop broad discovery once the entrypoint is clear.

This file is aligned with `resources/home/user/index/manifest.yml`.
