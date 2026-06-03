# Plan

Use this plan when implementing a new feature or significant enhancement.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/frameworks/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Requirements
- Clear user story or problem statement.
- Acceptance criteria with observable behavior.
- Compatibility and migration expectations (if any).

## Scope
- In: feature behavior, touchpoints, and tests.
- Out: unrelated refactors or platform upgrades.

## Delivery mode
- PoC mode: timebox to validate hypotheses and feasibility with explicit go/no-go criteria.
- Implementation mode: production-ready delivery with complete rollout, rollback, and operational readiness.

## PoC hypothesis and decision gate (required in PoC mode)
- <hypothesis and why this PoC de-risks implementation>
- <timebox start/end date and max acceptable effort/cost>
- <success thresholds and evidence collection method>
- <go/no-go owner and decision date>

## Dependencies and assumptions
- <internal/external dependencies and owners>
- <environment/access/tooling assumptions>
- <decision deadlines or approval checkpoints>

## Success metrics and exit criteria
- <business outcomes and user-impact metrics>
- <technical SLO/SLA, reliability, and performance targets>
- <go/no-go decision criteria and approver>

## Files and entry points
- <entry points to inspect>
- <files/modules likely to change>

## Data model / API changes
- <schemas/contracts affected>
- <versioning or compatibility notes>

- API surfaces: <OpenAPI/JSON schema contract, normalized error model (for example RFC 9457), and idempotency/retry policy>

## Action items
[ ] Choose delivery mode (PoC vs implementation) and define decision gate.
[ ] Define PoC hypothesis, timebox, evidence plan, and go/no-go owner when PoC mode is selected.
[ ] Confirm requirements, constraints, and non-goals.
[ ] Define measurable success metrics and exit criteria.
[ ] Inventory existing patterns and dependencies.
[ ] Design the minimal change set and interfaces.
[ ] Define API contract/error model/versioning if API or protocol surfaces change.
[ ] Implement core functionality.
[ ] Add or update tests (unit/integration/contract).
[ ] Verify non-functional targets (security/reliability/performance/operability).
[ ] Update $CODEX_HOME/docs/runbooks and user-facing notes.
[ ] Validate behavior end-to-end.

## Testing and validation
- <commands to run, ordered fast → comprehensive>
- <evidence required for PoC go/no-go or implementation launch>

## Rollout / migration
- <backward compatibility, flags, migrations, rollback>
- <phased rollout owners and post-deploy verification checkpoints>

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
- <correctness/security/perf risks>

## Examples

- Example objective: "Add <feature> with <acceptance criteria>."
- Example validation: "make test"

## Open questions
- <blocking questions if any>
