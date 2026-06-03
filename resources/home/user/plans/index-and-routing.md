# Plan

Use this plan when changing entrypoints, related links, or index routing.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Requirements
- Updated manifest entries with consistent metadata.
- Regenerated index artifacts and related blocks.

## Scope
- In: `$CODEX_HOME/index/manifest.yml`, `$CODEX_HOME/index/` entrypoints, `$CODEX_HOME/INDEX.md`.
- Out: content changes unrelated to routing.

## Files and entry points
- `$CODEX_HOME/index/manifest.yml`
- `$CODEX_HOME/index/pack/*.md`
- `$CODEX_HOME/index/core/*.md`
- `$CODEX_HOME/index/domains/*/*.md`
- `$CODEX_HOME/INDEX.md`

## Action items
[ ] Update `$CODEX_HOME/index/manifest.yml` entries and related links.
[ ] Add or adjust entrypoint files under `$CODEX_HOME/index/`.
[ ] Spot-check key entrypoints for link accuracy.

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
- Missing related blocks in new entrypoints.
- Invalid canonical/entrypoint paths.

## Examples

- Example objective: "Update a router, entrypoint, or related-link contract in the runtime pack."
- Example validation: "python3 -m unittest tests.test_runtime_pack_docs_contract tests.test_runtime_pack_structure_contract"

## Open questions
- None.
