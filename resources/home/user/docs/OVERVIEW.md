# docs/OVERVIEW.md
Purpose: serve as the docs hub and fallback navigation doc.
If `$CODEX_HOME/AGENTS.md` is already in context and you already have the right entrypoint, skip this file unless explicitly requested.


## Navigation
<!-- BEGIN:nav -->
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

Maintenance contract:
- Update docs in `$CODEX_HOME/docs/`.
- Treat `$CODEX_HOME/docs/` as the active runtime documentation tree.

## Multi-agent handoffs
- Share this entrypoint plus the AGENTS -> MEMORY -> INDEX -> plans/workflows -> skills -> `$CODEX_HOME/UNIX.md` -> entrypoint order with any agent you `spawn_agent`.
- Log the handoff (entrypoint + stop condition) and keep status visible via `send_input`/`wait`/`close_agent` so reviewers can trace who touched which doc.
- Use `$CODEX_HOME/MULTI_AGENT.md` to pick the coordinator, discovery, implementation, review, and test roles before launching parallel work.

## Stop conditions
- If you already picked a routing entrypoint, **stop** and follow it.


## Contents
<!-- BEGIN:contents -->
- `$CODEX_HOME/docs/containers/overview.md` — Containers overview
- `$CODEX_HOME/docs/desktop/overview.md` — Desktop stack overview
- `$CODEX_HOME/docs/filesystems/overview.md` — Filesystems overview
- `$CODEX_HOME/docs/infra/overview.md` — Infrastructure overview
- `$CODEX_HOME/docs/lang/overview.md` — Languages overview
- `$CODEX_HOME/docs/observability/overview.md` — Observability overview
- `$CODEX_HOME/docs/perf/overview.md` — Performance playbook
- `$CODEX_HOME/docs/security/overview.md` — Security overview
- `$CODEX_HOME/docs/style/overview.md` — Style guides
- `$CODEX_HOME/docs/system/overview.md` — Host hardening overview
- `$CODEX_HOME/docs/systemd/overview.md` — systemd overview
- `$CODEX_HOME/docs/templates/overview.md` — Templates overview
- `$CODEX_HOME/docs/virtualization/overview.md` — Virtualization overview
- `$CODEX_HOME/docs/vscode/overview.md` — VS Code overview
- `$CODEX_HOME/docs/web/overview.md` — Web frameworks overview
- `$CODEX_HOME/docs/workflows/overview.md` — Workflows overview
- `$CODEX_HOME/docs/architecture.md` — Architecture notes
- `$CODEX_HOME/docs/prompt-writing.md` — Prompt writing
- `$CODEX_HOME/docs/prompts-maintenance.md` — Prompts maintenance
<!-- END:contents -->

## Start here (required order)
- `$CODEX_HOME/AGENTS.md` (authoritative global contract; mandatory first step)
- `$CODEX_HOME/memories/MEMORY.md` (load namespace guidance before routing)
- `$CODEX_HOME/INDEX.md`
- `$CODEX_HOME/index/pack/plans.md` + `$CODEX_HOME/index/pack/workflows.md`
- `$CODEX_HOME/index/pack/skills.md`
- follow `$CODEX_HOME/UNIX.md` before running commands
- `$CODEX_HOME/index/pack/docs.md`

## Pack discovery order (only after choosing pack scope)
- 1) Plans + Workflows → `$CODEX_HOME/index/pack/plans.md`, `$CODEX_HOME/index/pack/workflows.md`
- 2) Skills → `$CODEX_HOME/index/pack/skills.md`
- 3) Shell guide → read `$CODEX_HOME/UNIX.md`
- 4) Templates → `$CODEX_HOME/index/pack/templates.md`
- 5) Snippets → `$CODEX_HOME/index/pack/snippets.md`
- 6) Docs → `$CODEX_HOME/index/pack/docs.md`
- 7) Prompts → `$CODEX_HOME/index/pack/prompts.md`

## Fast onboarding catalogs
- Runtime prompts hub: `$CODEX_HOME/prompts/OVERVIEW.md`
- Runtime snippets hub: `$CODEX_HOME/snippets/OVERVIEW.md`
- Runtime templates hub: `$CODEX_HOME/templates/OVERVIEW.md`
- Runtime skill roots: `$CODEX_SKILLS` and the managed admin skill root
- Plugin runtime guide: `$CODEX_HOME/docs/plugins.md`
- Runtime multi-agent guide: `$CODEX_HOME/MULTI_AGENT.md`

## Core entrypoints (stable links)
- `$CODEX_HOME/index/core/security.md`
- `$CODEX_HOME/index/core/testing.md`
- `$CODEX_HOME/index/core/ci-cd.md`
- `$CODEX_HOME/index/core/perf.md`
- `$CODEX_HOME/index/core/plan.md`
- `$CODEX_HOME/index/core/repo-ops.md`
- `$CODEX_HOME/index/core/review-hardening.md`
- `$CODEX_HOME/index/core/supply-chain.md`
- `$CODEX_HOME/index/core/execpolicy.md`

## Domain routers
- `$CODEX_HOME/index/domains/system/overview.md`
- `$CODEX_HOME/index/domains/infra/overview.md`
- `$CODEX_HOME/index/domains/observability/overview.md`
- `$CODEX_HOME/index/domains/web/overview.md`
- `$CODEX_HOME/index/domains/lang/overview.md`
- `$CODEX_HOME/index/domains/desktop/overview.md`
- `$CODEX_HOME/index/domains/vscode/overview.md`

## Pack hubs
- `$CODEX_HOME/index/pack/config.md`
- `$CODEX_HOME/index/pack/docs.md`
- `$CODEX_HOME/index/pack/plans.md`
- `$CODEX_HOME/index/pack/prompts.md`
- `$CODEX_HOME/index/pack/workflows.md`
- `$CODEX_HOME/index/pack/templates.md`
- `$CODEX_HOME/index/pack/snippets.md`
- `$CODEX_HOME/index/pack/skills.md`
- `$CODEX_HOME/index/pack/style.md`
- `$CODEX_HOME/index/pack/rules.md`
- `$CODEX_HOME/index/pack/plugins.md`

## Writing docs that agents love
- Keep files small and focused (fast to load).
- Use clear headings and explicit “how to” steps.
- Include exact commands for build/test/run.
- Prefer contracts/invariants: what must not break.
- For long docs, start with a short summary and link to deeper sections.

## General references
- `architecture.md`
- `$CODEX_HOME/MULTI_AGENT.md`

## Runtime maintenance
- `$CODEX_HOME/config.toml`
- `$CODEX_HOME/.agents/plugins/marketplace.json`
- `$CODEX_HOME/plugins/cache/`
- After runtime doc edits, run the narrowest relevant validation and link checks for the active Codex installation.
