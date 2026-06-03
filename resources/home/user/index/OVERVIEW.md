# Index navigation (OVERVIEW)
Purpose: help the agent choose the **single correct next entrypoint** without flooding context.


## Navigation
<!-- BEGIN:nav -->
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Routing steps (stop once you have one entrypoint)
1) Identify scope:
   - Pack maintenance → `$CODEX_HOME/index/pack/overview.md`
   - Domain/tooling-specific → `$CODEX_HOME/index/domains/overview.md`
   - Workflow-level or unclear → `$CODEX_HOME/index/core/overview.md`
   - Language/shell conventions only → `$CODEX_HOME/index/style/overview.md`
2) Open exactly one router.
3) Open exactly one entrypoint from that router.
4) Follow that entrypoint; open deep docs only when it explicitly directs you.

## Required context
1) `$CODEX_HOME/AGENTS.md`
2) `$CODEX_HOME/memories/MEMORY.md` (use `default` when uncertain)
3) `$CODEX_HOME/INDEX.md`
4) `$CODEX_HOME/index/pack/plans.md` + `$CODEX_HOME/index/pack/workflows.md`
5) `$CODEX_HOME/index/pack/skills.md`
6) follow `$CODEX_HOME/UNIX.md` before executing commands

## Router shortcuts
- `$CODEX_HOME/index/core/overview.md` — workflow-level guidance.
- `$CODEX_HOME/index/domains/overview.md` — platform/tooling-specific routing.
- `$CODEX_HOME/index/pack/overview.md` — pack maintenance and catalogs.
- `$CODEX_HOME/index/style/overview.md` — language and shell conventions.

## Stop conditions
- Do **not** open multiple routers for one task.
- Do **not** open multiple entrypoints unless scope changes.
- If scope changes, restart at **Routing step 1**.





## Contents
<!-- BEGIN:contents -->
- `$CODEX_HOME/index/core/overview.md` — Core routing (overview)
- `$CODEX_HOME/index/domains/overview.md` — Domains routing (overview)
- `$CODEX_HOME/index/pack/overview.md` — Pack hubs routing (overview)
- `$CODEX_HOME/index/style/overview.md` — Style routing (overview)
<!-- END:contents -->

## Multi-agent handoffs
- Assign one entrypoint per agent and keep AGENTS -> MEMORY -> INDEX -> plans/workflows -> skills -> `$CODEX_HOME/UNIX.md` -> entrypoint order explicit.
- Use `$CODEX_HOME/MULTI_AGENT.md` to choose the correct role before delegating.
- Track handoff status via `send_input`/`wait`/`close_agent`.
- For orchestration-heavy work, use `$CODEX_HOME/index/core/agent-orchestration.md`.

## Pack maintainer notes
- `manifest.yml` is the source of truth for entrypoints and related links.
- Keep affected entrypoints and related-link blocks in sync in the same change.
- After manifest edits, run targeted validation and a focused `rg -n --sort path --color=never` sweep for stale routing references in the active Codex installation.
