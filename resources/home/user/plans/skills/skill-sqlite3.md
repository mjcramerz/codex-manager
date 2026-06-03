# Plan

Use this plan when applying or updating the `sqlite3` skill.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/skills/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Inputs
- Use skill sqlite3.
- Any referenced scripts, assets, or references in the skill

## Scope
- In: tasks covered by the `sqlite3` skill and its resources.
- Out: tasks outside the skill’s domain.

- For API/protocol surfaces, define contract versioning, timeout/retry ceilings, and idempotency/error-model expectations.

## Action items
[ ] Use skill sqlite3 and linked resources.
[ ] Collect required inputs (paths, constraints, desired output).
[ ] Confirm database path, access mode, and mutation boundaries before running commands.
[ ] Execute the skill workflow and produce outputs.
[ ] Validate outputs and update links/backlinks if applicable.

## Testing and validation
- Follow validation steps in the skill or linked docs.

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
- Database locks, journaling mode, or file-copy backups may invalidate assumptions.
- Large scans or integrity checks can be too expensive for the active runtime budget.

## Examples

- Example objective: "Diagnose a slow query in a local SQLite database"
- Example validation: "`sqlite3 -readonly app.db 'EXPLAIN QUERY PLAN SELECT * FROM events LIMIT 10;'`"

## Open questions
- None.
