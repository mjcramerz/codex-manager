# Architecture notes
Purpose: a minimal, scalable architecture pattern for APIs, CLIs, and services.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## When to use
- bootstrapping a new service or major refactor
- clarifying boundaries for validation, auth, and persistence

## Layers (default model)
1) **Interfaces** (HTTP/CLI): parse, validate, auth, map errors
2) **Application services**: orchestrate workflows, transactions, policies
3) **Domain**: pure logic, invariants, types
4) **Infrastructure**: DB, network clients, filesystem, queues

## Rules of thumb
- Keep the domain pure and testable.
- Keep I/O at boundaries; avoid leaking transport concerns into core logic.
- Make errors explicit and typed; avoid leaking internals across boundaries.
- Make configuration explicit and validated at startup.
- Observability is first-class: logs, traces, metrics.
- Put security controls at trust boundaries (validation, authz, size/time limits).

See also:
- `workflows/build-an-app.md`
- `security/overview.md`
- `perf/overview.md`
- `style/overview.md`
- `$CODEX_HOME/index/pack/docs.md`
