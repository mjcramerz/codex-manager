# Plan

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/frameworks/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Requirements
- <outcome to ship>
- <data integrity and backward-compatibility requirements>
- <downtime window and compliance constraints>

## Scope
- In: <what changes>
- Out: <what must not change>

## Constraints / Non-goals
- <constraints, safety limits, deadlines>

## Dependencies and assumptions
- <upstream/downstream dependencies and owners>
- <environment/access assumptions>
- <backup/restore and audit evidence assumptions>

## Success metrics and exit criteria
- <migration correctness and data-quality metrics>
- <runtime performance/error-budget targets after cutover>
- <go/no-go criteria and owner sign-off>

## Current state (inventory)
- <files/modules/services>
- <data stores/schemas/contracts>
- <deployment/ops touchpoints>

## Action items
[ ] Define migration boundaries (`<files>`) and compatibility guardrails.
[ ] Implement forward migration (`<files>`) with bounded execution and retries.
[ ] Implement backward migration or safe fallback (`<files>`).
[ ] Add feature flags/guards and progressive rollout controls (`<files>`).
[ ] Execute rehearsal or dry-run in staging and capture evidence.
[ ] Update $CODEX_HOME/docs/runbooks and operator checklists.

## Testing and validation
- <commands to run, ordered fast → comprehensive>
- <acceptance criteria>

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

## Risks / Rollback
- <data safety, compatibility, rollback plan>

## References
- <tickets, specs, links, files>

## Examples

- Example objective: "Migrate <data/system> with rollback."
- Example validation: "<migration verify command>"
