# Multi-Agent Guide

Use this guide when the task is large enough to justify multiple spawned agents.
Role definitions live in `$CODEX_HOME/config.toml` under `[agents.*]`, and each role-specific config layer is rendered into `$CODEX_AGENTS/*.toml`.

## Routing Order
- Follow `$CODEX_HOME/AGENTS.md`.
- Load `$CODEX_HOME/memories/MEMORY.md` when the task is repo-aware or depends on prior decisions.
- Route through `$CODEX_HOME/INDEX.md`.
- Read `$CODEX_HOME/index/pack/plans.md` and `$CODEX_HOME/index/pack/workflows.md`.
- Load the minimum required skills.
- Follow `$CODEX_HOME/UNIX.md` before running shell-sensitive commands.

## Role Selection
- `default` — baseline single-owner role for routine coding, config edits, and small integration work.
- `manager` — planning and gating role; owns task lists, acceptance criteria, artifact checks, and role handoffs.
- `worker` — bounded execution role for narrow tasks with explicit stop conditions.
- `coder` — main implementation role for code changes, refactors, and root-cause fixes.
- `integrator` — read-first repo-ops role for mirror-sync checks, patch-readiness checks, and release handoff validation.
- `hunter` — web-search and source-comparison role for current docs, live APIs, and external evidence.
- `explorer` — read-heavy repo mapping role for architecture tracing, dependency discovery, and codebase reconnaissance.
- `reviewer` — review role for syntax, hardening, regressions, correctness, and best-practice checks.
- `tester` — validation role for targeted tests, failure-path checks, and release-confidence reporting.

## Recommended Flows
- Small change: `default` -> `reviewer` -> `tester`
- Cross-cutting repo change: `manager` -> `explorer` -> `coder` -> `reviewer` -> `tester`
- Current-info task: `manager` -> `hunter` -> `worker` -> `reviewer`
- Release or patch-readiness task: `manager` -> `explorer` -> `integrator` -> `reviewer` -> `tester`
- Parallel multi-slice task: `manager` assigns disjoint file ownership, then reconciles `worker` or `coder` outputs before review and testing

## Handoff Contract
- State the objective, owned files, and stop condition.
- Name the entrypoint, workflow, and validation commands the receiving role must follow.
- Include assumptions, artifacts produced, and any unresolved risks.
- Require evidence before handoff: command output, parser checks, screenshots, or diff references as applicable.
- Do not hand off partially verified release, patch, or migration work without explicit risk notes.

## Role Guardrails
- `manager` must not hand off implementation until requirements and acceptance criteria are explicit.
- `explorer` and `hunter` should stay read-first; they produce evidence and route guidance before mutation-heavy work begins.
- `coder` and `worker` should stay inside their owned slice and avoid stealing review or test ownership.
- `reviewer` should focus on correctness, hardening, regressions, and remediation-first findings.
- `tester` should run the narrowest convincing validation first, then expand only when risk demands it.
- `integrator` should check mirror sync and patch applicability, but should not apply release patches permanently unless the user explicitly asks for that mutation.

## Completion Gates
- Review is complete when `reviewer` reports severity-ranked findings or explicitly clears the change.
- Testing is complete when `tester` reports exact commands, outcomes, and skipped checks.
- Integration is complete when `integrator` confirms mirror and patch-readiness evidence or documents the blocker precisely.
- The overall task is complete only after `manager` or the coordinating role confirms artifacts exist for every handoff and the final risk list is explicit.
