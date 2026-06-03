# Plan

Use this plan when applying or updating the `c2-defense-ops` skill.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/skills/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Inputs
- Use skill c2-defense-ops.
- Any referenced scripts, assets, or references in the skill

## Scope
- In: tasks covered by the `c2-defense-ops` skill and its resources.
- Out: out-of-scope C2 emulation or offensive activity outside the documented scope.

- For API/protocol surfaces, define contract versioning, timeout/retry ceilings, and idempotency/error-model expectations.

## Action items
[ ] Use skill c2-defense-ops and linked resources.
[ ] Validate documented scope and operation class before simulation.
[ ] Execute workflow steps and produce evidence-backed outputs.
[ ] Validate outputs and update linked docs/snippets/templates if needed.

## Testing and validation
- Follow validation steps in the skill or linked docs.

## Security checkpoints
- Confirm trust boundaries, credentials, and least-privilege assumptions before execution.
- Validate input bounds, timeout/retry limits, and failure behavior for risky operations.
- Record any documented exception, owner, and expiry before proceeding.

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
- Missing telemetry needed for high-confidence C2 detection validation.
- Scope mismatch between documented targets and tested infrastructure.

## Examples

- Example objective: "<short task statement>"
- Example validation: "<command or check>"

## Open questions
- None.
