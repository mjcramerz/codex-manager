# $CODEX_HOME/plans/ (OVERVIEW)
Plan templates for tasks that require plans across the pack and real-world workflows.

## Navigation
<!-- BEGIN:nav -->
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

Maintenance contract:
- Create/update plan templates in `$CODEX_HOME/plans/`.
- Treat `$CODEX_HOME/plans/` as runtime materialized content.

## How to use
- Pick the plan that matches the task type or surface area you are updating.
- Prefer workflows/plans first; use skills for complex, domain-specific tasks.
- Copy a plan into your working plan space if you need to customize it.
- Keep plan names stable and update frontmatter metadata when revising.
- If the task targets a repository rollout, reference `$CODEX_HOME/rollouts/<repo>/ROLLOUT_PLAN.md` and keep plan sequencing aligned.

## Required routing contract
- `$CODEX_HOME/AGENTS.md`
- `$CODEX_HOME/memories/MEMORY.md` (use `default` when uncertain)
- `$CODEX_HOME/INDEX.md`
- `$CODEX_HOME/index/pack/plans.md` + `$CODEX_HOME/index/pack/workflows.md`
- `$CODEX_HOME/index/pack/skills.md`
- follow `$CODEX_HOME/UNIX.md` before running commands

## Contents
<!-- BEGIN:contents -->
- `$CODEX_HOME/plans/frameworks/overview.md` — Plan frameworks (overview)
- `$CODEX_HOME/plans/skills/overview.md` — Skill plans (overview)
- `$CODEX_HOME/plans/workflows/overview.md` — Workflow plans (overview)
- `$CODEX_HOME/plans/docs-and-workflows.md` — Plan
- `$CODEX_HOME/plans/index-and-routing.md` — Plan
- `$CODEX_HOME/plans/pack-overview.md` — Plan
- `$CODEX_HOME/plans/prompts-library.md` — Plan
- `$CODEX_HOME/plans/rules-library.md` — Plan
- `$CODEX_HOME/plans/scripts-and-verification.md` — Plan
- `$CODEX_HOME/plans/skills-library.md` — Plan
- `$CODEX_HOME/plans/snippets-library.md` — Plan
- `$CODEX_HOME/plans/templates-library.md` — Plan
<!-- END:contents -->

## Plan required before coding
- Use the trigger list in `$CODEX_HOME/AGENTS.md` (canonical source).

## Plan schema (required sections)
A plan is a Markdown file that answers:
- **Objective**: what outcome are we shipping?
- **Scope**: what must change.
- **Constraints / Non-goals**: what must not change.
- **Current state (inventory)**: files/systems involved.
- **Plan (steps)**: ordered steps with checkpoints.
- **Validation (tests & checks)**: commands + acceptance criteria.
- **Risks / Rollback**: security/perf/rollback notes.
- **References**: files, links, tickets.

## Cross-project quality baseline (2026-02-25)
Apply these gates to every non-trivial plan (programming, integrations, API work, infra, and docs):
- **PoC readiness**: define hypothesis, measurable success metrics, timebox, constraints, and explicit go/no-go decision owner.
- **Integration/API readiness**: use contract-first planning (OpenAPI/JSON schema), define auth/scopes, retries/timeouts/backoff, idempotency behavior, and compatibility strategy.
- **Implementation readiness**: define phased milestones with owners, validation evidence per phase, and rollout/rollback triggers.
- **Operational readiness**: define observability (logs/metrics/traces/alerts), runbook updates, and failure-mode handling.
- **Security by design**: capture trust boundaries, least privilege, secret handling, and API abuse scenarios early.

- **API behavior on constrained networks**: define idempotency policy, timeout/retry ceilings, and normalized error responses (for example RFC 9457 Problem Details).

Step rules:
- Start each step with a verb.
- Point to the files it touches.
- State how to verify it.

## External references (latest reviewed 2026-02-25)
- Microsoft PoC guidance (updated 2025-05-13) with pilot sequencing (`Plan -> Design -> Explore implementation -> Collect insights -> Test -> Deploy -> Optimize -> Govern`): https://learn.microsoft.com/en-us/azure/app-modernization-guidance/launch/build-a-proof-of-concept
- Microsoft Synapse PoC playbook guidance for scoped, measurable, time-bounded PoCs with explicit timeboxing: https://learn.microsoft.com/en-us/azure/synapse-analytics/guidance/proof-of-concept-playbook-dedicated-sql-pool
- Microsoft API design best practices (REST, OpenAPI, and contract-first API planning; updated 2025-05-08): https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design
- OpenAPI Specification v3.2.0 (published 2025-09-19) guidance (`operationId` uniqueness, explicit responses/security schemes/servers, callbacks/webhooks): https://spec.openapis.org/oas/v3.2.0.html
- RFC 9457 (Problem Details for HTTP APIs) for interoperable API error contracts: https://datatracker.ietf.org/doc/rfc9457/
- AWS Well-Architected implementation guidance for iterative milestones and 90-180 day improvement windows: https://docs.aws.amazon.com/wellarchitected/latest/userguide/implement-and-track-improvements.html
- OWASP API Security Top 10 (2023) risk categories for API planning checklists: https://owasp.org/API-Security/editions/2023/en/0x00-header/
- CISA Secure by Design initiative guidance for product security outcomes: https://www.cisa.gov/securebydesign
- systemd `systemd.exec` hardening options reference for Linux service plans: https://www.freedesktop.org/software/systemd/man/systemd.exec.html

## If no template fits
- Create a new plan template in the correct folder:
  - `$CODEX_HOME/plans/frameworks/` for general task types (feature/bugfix/refactor/etc.)
  - `$CODEX_HOME/plans/workflows/` for workflow-specific work
  - `$CODEX_HOME/plans/skills/` for skill-driven work
- Use the closest existing plan as a base; keep steps small and dependency-ordered.
- Add the new plan to this overview list.

## Plan types to keep around
- **Feature plan**: user story, acceptance criteria, rollout plan.
- **Refactor plan**: invariants, benchmarks, regression tests.
- **Migration plan**: forward/backward migration, data safety, rollback.
- **Incident/bug plan**: reproduction, minimal fix, tests.
- **Security hardening plan**: threat model, input boundaries, permission checks, logging hygiene.

## Plan categories
- `$CODEX_HOME/plans/frameworks/` — common task types (feature, bugfix, refactor, migration, security, perf, infra, docs)
- `$CODEX_HOME/plans/skills/` — plan templates for every skill
- `$CODEX_HOME/plans/workflows/` — plan templates for every workflow
- Pack maintenance plans:
  - `pack-overview.md`
  - `index-and-routing.md`
  - `docs-and-workflows.md`
  - `prompts-library.md`
  - `skills-library.md`
  - `templates-library.md`
  - `snippets-library.md`
  - `rules-library.md`
  - `scripts-and-verification.md`

## Framework templates (common)
- `$CODEX_HOME/plans/frameworks/plan-feature-delivery.md`
- `$CODEX_HOME/plans/frameworks/plan-bugfix.md`
- `$CODEX_HOME/plans/frameworks/plan-refactor.md`
- `$CODEX_HOME/plans/frameworks/plan-migration.md`
- `$CODEX_HOME/plans/frameworks/plan-security-hardening.md`
- `$CODEX_HOME/plans/frameworks/plan-performance.md`
- `$CODEX_HOME/plans/frameworks/plan-infra-change.md`
- `$CODEX_HOME/plans/frameworks/plan-docs-and-runbook.md`
- `$CODEX_HOME/plans/frameworks/plan-integration.md`

## Security checkpoints
- Confirm trust boundaries, credentials, and least-privilege assumptions before execution.
- Validate input bounds, timeout/retry limits, and failure behavior for risky operations.
- Record any approved exception, owner, and expiry before proceeding.

## Testing checkpoints
- Define fast-path and deep validation commands before making changes.
- Capture expected outcomes and acceptance criteria for each validation step.
- Re-run impacted checks after major changes and before final handoff.

## Deployment checkpoints
- Document rollout order, blast-radius controls, and rollback conditions.
- Confirm migration/backfill or feature-flag sequencing when applicable.
- Record post-deploy verification owners and evidence.
- When a repository has a rollout folder under `$CODEX_HOME/rollouts/`, link that `ROLLOUT_PLAN.md` explicitly in the plan output.

## Multi-agent handoff
- Share this entrypoint plus the AGENTS -> MEMORY -> INDEX -> plans/workflows -> skills -> `$CODEX_HOME/UNIX.md` -> entrypoint order with any agent you `spawn_agent`.
- Use `$CODEX_HOME/MULTI_AGENT.md` to choose roles, stop conditions, and validation owners before delegation.
- Coordinator hands off scope, constraints, and stop condition with the target entrypoint.
- Executor reports touched files, commands run, evidence, blockers, and next action.
- Keep status visible with `send_input`/`wait`/`close_agent` so reviewers can trace ownership and progress.

## Related
- `$CODEX_HOME/index/pack/plans.md`
- `$CODEX_HOME/index/core/plan.md`

## Examples

- Example objective: "<short task statement>"
- Example validation: "<command or check>"
