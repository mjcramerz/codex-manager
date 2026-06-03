# Plan

Use this plan when restructuring code without changing external behavior.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/frameworks/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Requirements
- Behavior to preserve and invariants to maintain.
- Scope boundaries and success criteria.

## Scope
- In: targeted modules/components.
- Out: feature changes or large rewrites.

## Dependencies and assumptions
- <test coverage assumptions and quality gates>
- <shared component ownership and review dependencies>

## Success metrics and exit criteria
- <behavior preserved with passing regression suite>
- <maintainability improvements (complexity/churn/readability) with no SLA regressions>

## Files and entry points
- <modules to refactor>
- <tests that cover behavior>

## Action items
[ ] Define invariants and expected behavior.
[ ] Identify coupling points and safe seams.
[ ] Plan incremental refactor steps.
[ ] Apply refactor in small, reviewable chunks.
[ ] Update or add tests to lock behavior.
[ ] Validate performance and correctness.

## Testing and validation
- <commands to run, ordered fast → comprehensive>

## Rollback strategy
- <revert plan if refactor introduces regressions>

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
- <hidden dependencies, performance regressions>

## Examples

- Example objective: "Refactor <module> while preserving behavior."
- Example validation: "make check"

## Open questions
- <gaps in coverage or unclear invariants>
