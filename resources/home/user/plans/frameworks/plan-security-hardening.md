# Plan

Use this plan for security reviews, mitigations, and hardening changes.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/frameworks/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Requirements
- Threat model or risk statement.
- Security objectives and acceptance criteria.
- Compliance or policy constraints.

## Scope
- In: targeted attack surfaces and mitigations.
- Out: unrelated feature or refactor work.

- API-facing surfaces: map controls against OWASP API Security Top 10 (2023) categories.

## Dependencies and assumptions
- <required security tooling, telemetry, and access>
- <policy/compliance stakeholders and approval dependencies>

## Success metrics and exit criteria
- <risk reduction metrics and control coverage targets>
- <validation evidence required for sign-off (tests/scans/reviews)>
- <incident-response and rollback readiness criteria>

## Files and entry points
- <security-sensitive boundaries>
- <auth/authz or input validation points>

## Action items
[ ] Identify primary threats and abuse cases.
[ ] Map target controls to OWASP API Top 10 and (when applicable) NISTIR 8259A baseline capabilities.
[ ] Review current controls and gaps.
[ ] Design mitigations (validation, auth, limits, logging).
[ ] Implement changes with safe defaults.
[ ] Add negative tests and regression coverage.
[ ] Update security $CODEX_HOME/docs/runbooks.

## Testing and validation
- <security tests, linters, scans>

## Rollout / monitoring
- <staged rollout, alerting, incident response>

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
- <false positives/negatives, bypass risks>

## Examples

- Example objective: "Harden <surface> against <threat>."
- Example validation: "<security test or scan>"

## Open questions
- <policy or threat model gaps>
