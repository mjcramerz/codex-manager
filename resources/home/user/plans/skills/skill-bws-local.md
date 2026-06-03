# Plan

Use this plan when applying or updating the `bws-local` skill.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/skills/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Inputs
- Use skill bws-local.
- Any referenced scripts, assets, or references in the skill.

## Scope
- In: local BWS install/config/keyring lifecycle tasks defined by the skill.
- Out: CI/CD pipeline-level BWS integrations.

- For API/protocol surfaces, define contract versioning, timeout/retry ceilings, and idempotency/error-model expectations.

## Action items
[ ] Use skill bws-local and linked resources.
[ ] Collect required host constraints (Debian version, shell model, privilege boundaries).
[ ] Execute the skill workflow with local-only scope.
[ ] Validate outputs and cross-link docs/prompts/index references if changed.

## Testing and validation
- Follow validation steps in the skill or linked docs.

## Security checkpoints
- Confirm trust boundaries, credentials, and least-privilege assumptions before execution.
- Validate input bounds, timeout/retry limits, and failure behavior for keyring and sudo operations.
- Record any approved exception, owner, and expiry before proceeding.

## Testing checkpoints
- Define fast-path and deep validation commands before making changes.
- Capture expected outcomes and acceptance criteria for each validation step.
- Re-run impacted checks after major changes and before final handoff.

## Deployment checkpoints
- Document rollout order, blast-radius controls, and rollback conditions.
- Confirm teardown path removes local binary/path/keyring state completely.
- Record post-deploy verification owners and evidence.

## Multi-agent handoff
- Coordinator hands off scope, constraints, and stop condition with the target entrypoint.
- Executor reports touched files, commands run, evidence, blockers, and next action.
- Receiving agent acknowledges handoff completeness before continuing execution.

## Risks and edge cases
- DBus/session keyring bootstrap may differ across local shell/session types.
- PATH visibility may lag until login shell refresh.
- Root-invoked workflows can target wrong keyring user without explicit owner mapping.

## Examples

- Example objective: "Harden local bws install + keyring lifecycle for Debian workstation."
- Example validation: "`make check && make install && make keyring-status`"

## Open questions
- None.
