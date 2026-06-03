# Plan

Use this plan when following `$CODEX_HOME/docs/workflows/agent-orchestration.md`.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/workflows/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Inputs
- `$CODEX_HOME/docs/workflows/agent-orchestration.md`
- `$CODEX_HOME/MULTI_AGENT.md`
- Active task objective, acceptance criteria, and constraints

## Scope
- In: multi-agent decomposition, ownership boundaries, and reconciliation workflow.
- Out: implementation details not needed for coordination design.

- For API/protocol surfaces, define contract versioning, timeout/retry ceilings, and idempotency/error-model expectations.

## Action items
[ ] Read `$CODEX_HOME/docs/workflows/agent-orchestration.md` and related references.
[ ] Read `$CODEX_HOME/MULTI_AGENT.md` and pick the coordinator plus execution roles.
[ ] Decompose work into independent tracks with explicit file ownership.
[ ] Assign each track a role, entrypoint, stop condition, and verification expectations.
[ ] Execute tracks and collect structured handoff summaries.
[ ] Reconcile outputs, resolve overlaps, and produce final verification evidence.

## Testing and validation
- Verify each track includes relevant test/lint/build evidence.
- Run coordinator-level verification covering all touched subsystems.

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
- Overlapping ownership causing conflicting edits.
- Missing handoff details that block final verification.

## Examples

- Example objective: "Split pack-wide refactor into routing, scripts, and skills tracks."
- Example validation: "All track checks pass and coordinator publishes consolidated evidence."

## Open questions
- None.
