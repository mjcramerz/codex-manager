# Plan frameworks (overview)
Reusable plan templates for common plan-required task types.

## Contents
<!-- BEGIN:contents -->
- `$CODEX_HOME/plans/frameworks/plan-bugfix.md` — Plan
- `$CODEX_HOME/plans/frameworks/plan-docs-and-runbook.md` — Plan
- `$CODEX_HOME/plans/frameworks/plan-feature-delivery.md` — Plan
- `$CODEX_HOME/plans/frameworks/plan-infra-change.md` — Plan
- `$CODEX_HOME/plans/frameworks/plan-integration.md` — Plan
- `$CODEX_HOME/plans/frameworks/plan-migration.md` — Plan
- `$CODEX_HOME/plans/frameworks/plan-performance.md` — Plan
- `$CODEX_HOME/plans/frameworks/plan-refactor.md` — Plan
- `$CODEX_HOME/plans/frameworks/plan-security-hardening.md` — Plan
<!-- END:contents -->

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Use these when
- the task does not cleanly map to a specific workflow or skill
- you need a concrete plan structure quickly
- you want a consistent checklist for reviews and execution
- any multi-file refactor is required
- any plan-before-coding trigger applies

## Plan mode selection
- **PoC-first work**: use `plan-feature-delivery.md` with a timeboxed hypothesis and explicit go/no-go exit criteria.
- **Integration/API delivery**: use `plan-integration.md` and require API contract, auth scope, reliability, and observability checkpoints.
- **Implementation delivery**: use `plan-feature-delivery.md`, `plan-infra-change.md`, or `plan-migration.md` with phased rollout, owners, and rollback evidence.

## Universal quality gates
- Include dependencies and assumptions (owners, environments, external systems).
- Include measurable success metrics and explicit exit criteria.
- Include non-functional expectations (security, reliability, performance, maintainability).
- Include staged validation and rollout checkpoints with evidence capture.
- Include failure handling, rollback, and operational runbook updates.

- Infrastructure and service plans should explicitly evaluate `systemd` hardening controls when applicable.
- Integration/API plans should include contract versioning, idempotency strategy, and constrained-network retry limits.

## Frameworks
- `plan-feature-delivery.md` — new features and enhancements
- `plan-bugfix.md` — defect investigation and fixes
- `plan-refactor.md` — behavior-preserving structure changes
- `plan-migration.md` — migrations and data/schema changes
- `plan-integration.md` — external API or service integrations
- `plan-security-hardening.md` — security posture improvements
- `plan-performance.md` — profiling and optimization work
- `plan-infra-change.md` — infrastructure and ops changes
- `plan-docs-and-runbook.md` — documentation and runbook updates

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

## Multi-agent handoff
- Coordinator hands off scope, constraints, and stop condition with the target entrypoint.
- Executor reports touched files, commands run, evidence, blockers, and next action.
- Receiving agent acknowledges handoff completeness before continuing execution.

## Related
- `../OVERVIEW.md`
- `$CODEX_HOME/docs/workflows/planning.md`

## Examples

- Example objective: "<short task statement>"
- Example validation: "<command or check>"
