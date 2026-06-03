# Plan

Use this plan when diagnosing and fixing a bug or regression.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/frameworks/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Requirements
- Repro steps or failing test case.
- Expected vs actual behavior.
- Impact and urgency assessment.

## Scope
- In: fix, tests, and minimal supporting changes.
- Out: unrelated refactors or feature work.

## Dependencies and assumptions
- <systems/environments needed to reproduce and validate>
- <required access, logs, and telemetry availability>

## Success metrics and exit criteria
- <repro no longer fails and regression coverage exists>
- <error-rate/performance impact within acceptable bounds>
- <decision owner for release readiness>

## Files and entry points
- <repro entry points>
- <files likely involved>

## Action items
[ ] Reproduce the issue and capture evidence.
[ ] Identify root cause and affected paths.
[ ] Design a minimal, safe fix.
[ ] Implement the fix with guardrails.
[ ] Add regression tests.
[ ] Validate against repro and related cases.
[ ] Document findings if user-facing or operational.

## Testing and validation
- <commands to run, ordered fast → comprehensive>

## Rollout / mitigation
- <rollback plan or mitigations if needed>

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
- <related behaviors that could regress>

## Examples

- Example objective: "Fix crash in <component> when <trigger>."
- Example validation: "cargo test <module>::<test_name>"

## Open questions
- <missing inputs if any>
