---
title: AGENTS.md (global Codex agent contract)
status: active
owner: Matthew Cramer
tags:
- home
- agents-md
- codex
updated: 2026-06-28
---
# Global Codex agent contract
Purpose: tell the Codex coding agent exactly how to route work under `$CODEX_HOME/**`, how to decide what is editable, and how to stop unsafe or out-of-scope mutations.

This contract applies to `$CODEX_HOME` and every child path unless a deeper `AGENTS.md` overrides it.

## Mission
- You must use `$CODEX_HOME` as your operating handbook for routing, workflows, plans, rules, snippets, and templates.
- You must route quickly, choose one concrete entrypoint, and stop broad browsing once the next action is clear.
- You must preserve user intent, keep diffs reviewable, and prefer high-signal instructions over long narrative overviews.

## Priorities
1) Correctness
2) Security
3) Maintainability
4) Performance
5) Polish

## Authority and scope
- You must follow this precedence order: system -> developer -> user -> this file -> deeper instructions.
- You must preserve behavior unless the user explicitly asks you to change it.
- You must apply every active instruction file that covers a touched path.
- You must treat unexpected local edits as authoritative user state and work with them instead of reverting them.

## Mandatory startup order
1) You must read the active `AGENTS.md` first.
2) You must load `$CODEX_HOME/memories/` only when the task is repo-aware, ambiguous, or depends on prior decisions.
3) You must route through `$CODEX_HOME/INDEX.md`.
4) You must open `$CODEX_HOME/index/pack/plans.md` and `$CODEX_HOME/index/pack/workflows.md` before large or cross-cutting work.
5) You must load only the minimum required skills.
6) You must follow `$CODEX_HOME/docs/style/shell-runtime.md` before shell-sensitive work.
7) You must open one concrete workflow, plan, or style entrypoint and stop broad discovery.

## Routing contract
- You must start from `$CODEX_HOME/INDEX.md` and choose exactly one router before opening deep material.
- You must use `$CODEX_HOME/docs/workflows/overview.md` when the task needs a procedure.
- You must use `$CODEX_HOME/plans/OVERVIEW.md` when the task is multi-step, ambiguous, or large enough to justify an explicit plan.
- You must use `$CODEX_HOME/docs/OVERVIEW.md`, `$CODEX_HOME/snippets/OVERVIEW.md`, and `$CODEX_HOME/templates/OVERVIEW.md` only after you know which surface you need.
- You must use installed runtime paths in your guidance and must not teach from repository-source paths unless the repository itself is the subject of the task.

## Repo write boundary rules
- You must inspect the current branch before mutating a repository.
- You must treat branches named `gitlab/*` and `github/*` as fork or mirror branches that are read-only by default.
- You must not make direct code edits on those fork or mirror branches.
- You must treat `mcr/main` as the only writable branch for the restricted fork workflow described here.
- When you are on `mcr/main`, you may edit only the following repository-root surfaces unless a deeper repo contract explicitly grants more:
  - `AGENTS.override.md`
  - `.gitlab-ci.yml`
  - `.cirrus.yml`
  - `Makefile`
  - `justfile`
  - `.github/*`
  - `scripts/release/*`
  - `patches/release/*`
  - `.mcr/*`
  - `.circleci/*`
  - `.devcontainer/*`
  - `.vscode/*`
  - `.codex/*`
  - `.agents/*`
  - `debian/*`
  - `.bazelversion`
  - `.bazelignore`
  - `.bazelrc`
  - `bazel/*`
- If the user asks for code changes outside that allowlist while you are on a fork or mirror workflow, you must stop, explain the boundary, and require a writable branch or repo contract before continuing.

## Debian packaging rule
- If a repository root contains `debian/`, you must treat that repository as a Debian package source tree.
- After that, you must inspect `debian/`, `.gitlab-ci.yml`, `Makefile`, `justfile`, and any release or patch surfaces before touching packaging behavior.
- You must assume the GitLab pipeline may publish packages to Aptly or OBS and therefore must preserve package metadata, changelog flow, versioning, and publish-job contracts.

## Multi-agent rules
- You must stay single-owner by default.
- You may fan out only when the user explicitly asks for parallel agent work or when the active runtime contract explicitly enables it for the current task.
- You must keep one coordinating owner for final edits, validation, and handoff quality.
- Before delegating, you must write down the objective, owned files, stop condition, required workflow, and validation command for each child.
- You must keep read-only discovery and evidence gathering separate from mutation-heavy ownership whenever that reduces overlap.
- You must reconcile child findings before final edits, and you must not hand off anonymous summaries without provenance.
- You must prefer this role pattern when it fits the task:
  - `planner` for decomposition and acceptance criteria
  - `orchestrator` or `delegator` for thread control
  - `explorer` or `hunter` for read-only discovery
  - `coder` or `worker` for bounded implementation
  - `analyst` for conflict resolution
  - `reviewer` and `tester` for final gates

## Editing discipline
- You must prefer `rg` and `rg --files` for discovery.
- You must use `apply_patch` for focused manual edits.
- You may use deterministic scripts for broad, repetitive rewrites when scripting is safer than many hand edits.
- You must validate shape, size, ranges, and path boundaries for untrusted input before mutating files.
- You must re-parse edited JSON, YAML, and TOML before finishing the turn.
- You must keep generated `BEGIN` / `END` marker blocks syntactically intact when editing surrounding text.
- You must not invent compatibility branches, fallback paths, or legacy toggles unless the user explicitly asks for them.

## Validation rules
- You must run the narrowest checks that prove the change.
- When you touch `$CODEX_HOME/AGENTS.md`, `$CODEX_HOME/INDEX.md`, `$CODEX_HOME/docs/**`, `$CODEX_HOME/index/**`, `$CODEX_HOME/plans/**`, `$CODEX_HOME/snippets/**`, or `$CODEX_HOME/templates/**`, you must also run focused stale-link or structure checks.
- If you skip a check, you must say exactly why and name the next command that should run.

## Reference map
- `$CODEX_HOME/INDEX.md` is the top router.
- `$CODEX_HOME/memories/` is the repo-aware runtime memory surface.
- `$CODEX_HOME/docs/OVERVIEW.md` is the documentation hub.
- `$CODEX_HOME/docs/workflows/overview.md` is the workflow hub.
- `$CODEX_HOME/plans/OVERVIEW.md` is the planning hub.
- `$CODEX_HOME/rules/OVERVIEW.md` is the rule catalog.
- `$CODEX_HOME/snippets/OVERVIEW.md` is the reusable snippet catalog.
- `$CODEX_HOME/templates/OVERVIEW.md` is the reusable scaffold catalog.
- `$CODEX_HOME/docs/create-prompts.md` is the only prompt-file catalog you should cite from docs, index, plans, or templates.

## Output contract
- You must return: Summary -> Tests -> Risks/Follow-ups -> Next steps.
- You must include concrete file references with line numbers for the most important edits.
- You must state assumptions explicitly whenever behavior depends on credentials, permissions, external systems, or repo-ownership boundaries.
