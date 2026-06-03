# Plan

Use this plan when integrating with external APIs, SDKs, or services.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/frameworks/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Requirements
- API/spec details, auth requirements, and rate limits.
- Data contracts and error handling expectations.
- Security/privacy requirements.

## Scope
- In: integration surface, adapters, and tests.
- Out: unrelated feature work.

## Dependencies and assumptions
- <provider SLAs, ownership contacts, and escalation path>
- <credentials/scopes, network constraints, and environment parity assumptions>
- <upstream versioning, deprecation windows, and release cadence assumptions>

## Files and entry points
- <integration entry points>
- <config and secrets handling>

## Data model / API changes
- <new schema, DTOs, or configuration>

## API contract and compatibility
- <OpenAPI/JSON schema source and locked version>
- <operation mapping with unique operation IDs, explicit success/error responses, and pagination model>
- <backward-compatibility, version negotiation, and deprecation handling>
- <server URLs, security schemes/scopes, and callback/webhook contracts where applicable>

- Failure model: <timeout budget, retry/backoff ceilings, circuit-breaker thresholds, and dead-letter handling>

## Success metrics and exit criteria
- <latency/error-rate/reliability targets>
- <functional completion criteria for all required endpoint flows>
- <go/no-go criteria, fallback path, and owner sign-off>

## Action items
[ ] Review provider API docs/spec and identify required endpoints.
[ ] Capture contract-first interface (OpenAPI/JSON schema) and compatibility constraints.
[ ] Define auth/scopes, secret rotation expectations, and quota/rate-limit posture.
[ ] Define normalized error model (for example RFC 9457 Problem Details) and cross-system error mapping.
[ ] Define timeout, retry, and backoff policy with idempotency handling for retried writes.
[ ] Design integration boundary, fallback behavior, and error normalization model.
[ ] Implement adapters/clients with strict validation at trust boundaries.
[ ] Add tests (mocked, contract, sandbox) plus negative and resiliency scenarios.
[ ] Define observability (logs/metrics/traces/alerts) and operational ownership.
[ ] Document configuration, incident handling, and rollback runbook.

## Testing and validation
- <commands to run, ordered fast → comprehensive>
- <sandbox or mock validation steps>
- <contract validation against OpenAPI/JSON schema>
- <chaos/failure-mode validation for dependency outages and partial failures>
- <offline/reconnect validation for constrained or intermittently connected environments>

## Rollout / monitoring
- <feature flags, canary, metrics/alerts>
- <kill switch and fallback mode with decision owner>

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
- <rate limits/quota exhaustion, partial failures, data drift, auth scope drift, replay/idempotency bugs>

## Examples

- Example objective: "Integrate <system> with <service>."
- Example validation: "<integration test command>"

## Open questions
- <missing API details or credentials>
