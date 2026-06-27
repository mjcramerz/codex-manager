---
title: AGENTS.md (global coding agent contract)
status: active
owner: Matthew Cramer
tags:
- home
- agents-md
- agents
updated: 2026-06-21
---
# Global coding agent contract
Purpose: define the top-level rules you follow when using the installed Codex pack under `$CODEX_HOME/**`.

This contract applies to `$CODEX_HOME` and every child path unless a deeper `AGENTS.md` overrides it.

## Mission
- Route quickly, choose the right entrypoint, and stop broad browsing once the correct workflow is clear.
- Treat this file as your global operating contract for routing, planning, workflows, validation, and worktree discipline.
- Prefer short, high-signal guidance over encyclopedic restatements.

## Priorities
1) Correctness
2) Security
3) Performance
4) Maintainability
5) Polish

## Authority and scope
- Follow this order: system -> developer -> user -> this file -> deeper instructions.
- Preserve behavior unless the request explicitly changes behavior.
- Keep diffs minimal, reviewable, and deterministic.
- Apply every active instruction file for each touched path.

## Required operating order
1) Read the active `AGENTS.md`.
2) Load `$CODEX_HOME/memories/MEMORY.md` only when the task is repo-aware, ambiguous, or depends on prior decisions.
3) Route through `$CODEX_HOME/INDEX.md`.
4) Read `$CODEX_HOME/index/pack/plans.md` and `$CODEX_HOME/index/pack/workflows.md`.
5) Load only the minimum skills required.
6) Follow `$CODEX_HOME/docs/style/shell-runtime.md` before shell-sensitive work.
7) Open one concrete entrypoint, then stop broad browsing.

## Routing rules
- Start with `$CODEX_HOME/INDEX.md` and choose one router before opening detailed material.
- Use `$CODEX_HOME/memories/MEMORY.md` only when prior decisions or repo context actually matter.
- Prefer one workflow and one plan template at a time unless the task clearly spans multiple surfaces.
- Use installed paths in guidance; do not teach from repository-source paths unless the repository itself is the subject.

## Reference map
- `$CODEX_HOME/INDEX.md` is the top router for the runtime pack.
- `$CODEX_HOME/memories/MEMORY.md` is the memory-entry router for repo-aware work.
- `$CODEX_HOME/docs/OVERVIEW.md` is the documentation hub.
- `$CODEX_HOME/docs/workflows/overview.md` is the workflow hub.
- `$CODEX_HOME/index/pack/plans.md` and `$CODEX_HOME/plans/OVERVIEW.md` are the planning entrypoints.
- `$CODEX_HOME/rules/OVERVIEW.md` is the rule catalog.
- `$CODEX_HOME/templates/OVERVIEW.md` and `$CODEX_HOME/snippets/OVERVIEW.md` are the scaffold/pattern catalogs.
- `$CODEX_HOME/MULTI_AGENT.md` is the coordination guide when multi-agent work is active.

## Workflow and planning rules
- If the task is multi-step, ambiguous, or cross-cutting, use a plan and keep it current.
- Choose one workflow before editing when the task matches a documented procedure.
- Keep overview files concise; route first, dive deeper only when necessary.
- Update cross-links in the same change when canonical paths or entrypoints move.

## Structured-format rules
- Validate shape, size, and ranges for untrusted inputs.
- Re-parse edited JSON, YAML, and TOML before finishing the turn.
- Keep comments out of files that claim to be strict JSON.
- Keep generated marker blocks (`BEGIN` / `END`) syntactically intact when editing surrounding text.

## Branch and worktree rules
- Check current branch and worktree state before mutating files.
- Treat unrelated local changes as user state and do not revert them without explicit approval.
- Do not rewrite default, protected, or mirror branches unless the user explicitly asks for that mutation.
- Prefer in-place, reviewable updates over destructive cleanup.

## Editing and tool discipline
- Prefer `rg` / `rg --files` for discovery.
- Use `apply_patch` for focused manual edits.
- Use deterministic scripts only when broad repetition makes them safer than manual patching.
- Do not invent fallback paths, compatibility branches, or legacy toggles unless explicitly requested.
- Load only the minimum skills required for the current task.
- Follow `$CODEX_HOME/docs/style/shell-runtime.md` before shell-sensitive execution.

## Validation requirements
- Run the narrowest checks that prove the change.
- When touching governing pack files (`$CODEX_HOME/AGENTS.md`, `$CODEX_HOME/INDEX.md`, `$CODEX_HOME/docs/**`, `$CODEX_HOME/index/**`, `$CODEX_HOME/plans/**`, `$CODEX_HOME/templates/**`, `$CODEX_SKILLS/**`), also run focused contract checks for stale links or structural drift.
- If you skip a check, say exactly why and name the next command that should run.

## Multi-agent rules
- Stay single-owner by default.
- If multi-agent work is active in the current session, follow `$CODEX_HOME/MULTI_AGENT.md` for role selection, handoff discipline, and completion gates.
- Keep handoffs explicit: objective, owned files, validation commands, assumptions, and residual risks.

## Output contract
- Return: Summary -> Tests -> Risks/Follow-ups -> Next steps.
- Include concrete file references with line numbers for the important edits.
- State assumptions explicitly when behavior depends on credentials, permissions, or optional runtime assets.
