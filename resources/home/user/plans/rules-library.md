# Plan

Use this plan when updating execpolicy rules or guidance.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Requirements
- Rules are documented with clear intent and ordering.
- Execpolicy docs and indexes are updated.

## Scope
- In: `$CODEX_HOME/rules/` and related $CODEX_HOME/docs/index entries.
- Out: unrelated pack changes.

## Files and entry points
- `$CODEX_HOME/rules/OVERVIEW.md`
- `$CODEX_HOME/index/pack/rules.md`
- `$CODEX_HOME/index/core/execpolicy.md`
- `$CODEX_HOME/docs/workflows/execpolicy.md`

## Action items
[ ] Add or update rule files with explicit intent and scope.
[ ] Update `$CODEX_HOME/rules/OVERVIEW.md` to document ordering and constraints.
[ ] Update execpolicy docs and index references.

## Testing and validation

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
- Rule ordering conflicts.
- Missing references in docs or index.

## Examples

- Example objective: "<short task statement>"
- Example validation: "<command or check>"

## Open questions
- None.
