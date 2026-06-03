# Plan

Use this plan when modifying infrastructure, deployment, or system services.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/frameworks/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Requirements
- Environment targets and constraints.
- Rollback requirements and downtime limits.
- Ownership and approvals (if required).

## Scope
- In: infra code, configs, services, and runbooks.
- Out: unrelated product feature changes.

## Dependencies and assumptions
- <target environments, ownership boundaries, and approvals>
- <network/storage/identity dependencies and constraints>
- <maintenance window and rollback prerequisites>

## Success metrics and exit criteria
- <availability/reliability/performance targets after change>
- <infrastructure drift checks and policy compliance criteria>
- <go/no-go criteria for promotion and owner sign-off>

## Files and entry points
- <infra configs/manifests>
- <service definitions and pipelines>

## Action items
[ ] Inventory current infra and dependencies.
[ ] Define desired state and compatibility constraints.
[ ] Plan rollout steps and rollback strategy.
[ ] Implement changes with least privilege and safety checks.
[ ] Update monitoring/alerts and runbooks.
[ ] Validate in staging or dry-run where possible.

## Testing and validation
- <linters, policy checks, staging deploys>

## Rollout / migration
- <phased rollout, backups, verification>

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

## Risks and edge cases
- <downtime, data loss, config drift>

## Examples

- Example objective: "Change <infra> with rollback steps."
- Example validation: "<infra validation>"

## Open questions
- <missing approvals or environment details>
