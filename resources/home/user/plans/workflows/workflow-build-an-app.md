# Plan

Use this plan when following `$CODEX_HOME/docs/workflows/build-an-app.md`.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/workflows/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Inputs
- `$CODEX_HOME/docs/workflows/build-an-app.md`

## Scope
- In: steps defined in the `build-an-app` workflow.
- Out: unrelated workflows or tooling.

- For API/protocol surfaces, define contract versioning, timeout/retry ceilings, and idempotency/error-model expectations.

## Action items
[ ] Read `$CODEX_HOME/docs/workflows/build-an-app.md` and related references.
[ ] Collect required inputs and constraints (stack, deployment target, auth/data boundaries, branch/release policy).
[ ] Confirm branch strategy (`mcr/feature/*` -> `mcr/main` -> `mcr/staging` -> `mcr/release`) and fork-mode mirror policy (`origin/github/mcr/main -> github/mcr/main -> mcr/main`, read-only `github/*`, patch checks on `mcr/main` only).
[ ] Confirm deterministic build/install commands and lockfile/toolchain pinning.
[ ] Confirm repo delivery layout and version script strategy when release automation is in scope (`<repo>/scripts/release/get_version.py`, `<repo>/scripts/release/bump_version.py`).
[ ] Execute the workflow steps in order.
[ ] Validate outputs and document results.

## Testing and validation
- Run validation steps specified by the workflow.

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
- Missing prerequisites or environment constraints.
- Workflow steps out of order for current context.

## Examples

- Example objective: "<short task statement>"
- Example validation: "<command or check>"

## Open questions
- None.
