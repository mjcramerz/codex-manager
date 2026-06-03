# Planning workflow

Start with `$CODEX_HOME/plans/workflows/workflow-planning.md` before executing this workflow.
Purpose: provide the canonical planning workflow for this pack.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/workflows/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Plan

See `overview.md` for workflow index.

## Required routing contract
- `$CODEX_HOME/AGENTS.md`
- `$CODEX_HOME/memories/MEMORY.md` (use `default` when uncertain)
- `$CODEX_HOME/INDEX.md`
- `$CODEX_HOME/index/pack/plans.md` + `$CODEX_HOME/index/pack/workflows.md`
- `$CODEX_HOME/index/pack/skills.md`
- follow `$CODEX_HOME/UNIX.md` before running commands

## Plan selection (quick guide)

- **Workflow-specific work**: use `$CODEX_HOME/plans/workflows/` (e.g., `workflow-<name>.md`).
- **Skill-driven work**: use `$CODEX_HOME/plans/skills/` (e.g., `skill-<name>.md`).
- **General engineering tasks**: use `$CODEX_HOME/plans/frameworks/` (feature, bugfix, refactor, security, perf, infra, docs).

## When a plan is required (before coding)
- Use the trigger list in `$CODEX_HOME/AGENTS.md` (canonical source).

## Plan schema (required sections)
A plan should include:
- **Objective**
- **Scope**
- **Constraints / Non-goals**
- **Current state (inventory)**
- **Plan (steps)**
- **Validation (tests & checks)**
- **Risks / Rollback**
- **References**

Step rules:
- Start each step with a verb.
- Point to files/modules it touches.
- State how to verify each step.

## Plan creation rules (when no template fits)
- Non-trivial tasks and **any multi-file refactor** require a plan.
- If no plan template fits:
  - Create a new template under `$CODEX_HOME/plans/frameworks/`, `$CODEX_HOME/plans/workflows/`, or `$CODEX_HOME/plans/skills/`.
  - Use the existing templates in that folder as structure and naming reference.
  - Add the new plan to `$CODEX_HOME/plans/OVERVIEW.md`.
  - For new workflow/skill plans, ensure the matching workflow/skill exists and is linked.

## 0) Restate the goal

- What are we building/fixing?
- What is explicitly out of scope?
- What does “done” mean (acceptance criteria)?

## 1) Discover (fast)

- Entry points: CLI, API routes, binaries, services
- Existing patterns: config, logging, error handling, tests, CI
- Constraints: OS, runtime, sandbox/network mode, time budget

## 2) Design (brief, concrete)

- Data model (types, schemas)
- Control flow / architecture (modules, boundaries)
- Security model (auth, input validation, rate limits)
- Ops model (config, observability, deploy)

## 3) Implementation plan (task list)

Each task should be:

- independently testable
- small enough to review
- ordered by dependency
- start with a verb
- reference files touched
- state how to verify

Example:

1. Add config layer + validation
2. Add core domain types + unit tests
3. Implement API endpoints + integration tests
4. Add auth middleware + security tests
5. Add CI workflow + linters + scanners
6. Add docs + runbook

## 4) Validation plan

- Tests to run (fast → comprehensive)
- Static analysis (lint, format, typecheck)
- Security checks (dependency audit, secret scan)
- Performance checks (benchmark/profiling if needed)

## 5) Rollout plan (if applicable)

- Backwards compatibility
- Migration steps
- Feature flags / toggles
- Monitoring and alerts

## Security checkpoints
- Add threat assumptions and privileged operations to the plan before implementation begins.
- Attach input bounds/timeouts to steps that touch I/O, parsing, or remote systems.
- Record waiver owner and expiry for every planned security exception.

## Testing checkpoints
- Every step includes a concrete verify command plus pass/fail expectation.
- For bugfix or hardening work, require at least one failing or abuse test in the plan.
- Define fast-path versus full-suite checkpoints for incremental validation.

## Deployment checkpoints
- Include rollout, rollback, and migration/flag steps when runtime behavior changes.
- Mark go/no-go gates and required evidence before staging/release promotion.
- Identify who confirms post-deploy health and where evidence is stored.

## Multi-agent handoff
- Coordinator assigns plan steps by owner with explicit dependency order.
- Executors update step status with evidence, blockers, and next action before handoff.
- Receiving agent acknowledges scope completeness (files, risks, tests) before continuing.

## References

- `overview.md`
- `codex-repo.md`
- `$CODEX_HOME/index/pack/workflows.md`
- `$CODEX_HOME/index/core/plan.md`
