# Plan

Use this plan when applying or updating the `nethunter-pixel9a` skill.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/skills/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Inputs
- Use skill nethunter-pixel9a.
- Any referenced scripts, assets, or references in the skill.

## Scope
- In: tasks covered by the `nethunter-pixel9a` skill and its resources.
- Out: rooting/flashing activity outside the documented device scope or unsupported non-lab operations.

- For API/protocol surfaces, define contract versioning, timeout/retry ceilings, and idempotency/error-model expectations.

## Action items
[ ] Use skill nethunter-pixel9a and linked resources.
[ ] Validate documented scope, device ownership, and operation class.
[ ] Execute root/porting procedure with deterministic evidence capture.
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
- Boot image mismatch with current slot.
- Unlock wipes unexpected data on incorrectly scoped devices.

## Examples

- Example objective: "Validate rooted Pixel 9a lab flow and NetHunter package readiness."
- Example validation: "Run scope guard + preflight snippet + rollback test."

## Open questions
- None.
