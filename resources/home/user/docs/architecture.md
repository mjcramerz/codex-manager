# Architecture notes
Purpose: provide a default architecture shape for services, CLIs, and integration-heavy runtime components.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Use when
- bootstrapping a new service or major refactor
- deciding where validation, policy, orchestration, and I/O boundaries belong
- reviewing whether a design mixes transport, business logic, and infrastructure too tightly

## Default layers
1. Interfaces: CLI, HTTP, hooks, or transport adapters
2. Application services: orchestration, workflow, and policy decisions
3. Domain: invariants, pure logic, and durable types
4. Infrastructure: storage, network clients, filesystem, queues, and external integrations

## Design rules
- Keep trust-boundary logic at the edge.
- Keep domain logic transport-agnostic when possible.
- Keep configuration explicit and validated at startup.
- Keep observability and error taxonomy deliberate rather than incidental.
- Keep long-running or side-effect-heavy operations behind explicit service boundaries.

## Review checklist
- Are inputs validated at the interface boundary?
- Are side effects isolated from pure logic?
- Are retries, timeouts, and cancellation rules explicit?
- Are security assumptions visible in the design?
- Is there one clear place for operational verification?

## Related
- `$CODEX_HOME/docs/workflows/build-an-app.md`
- `$CODEX_HOME/docs/security/overview.md`
- `$CODEX_HOME/docs/perf/overview.md`
- `$CODEX_HOME/docs/style/overview.md`
