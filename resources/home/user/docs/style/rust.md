# Rust style guide
Canonical Rust guidance for this pack. Follow repo-specific conventions first.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/style/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Baseline
- Prefer `#![forbid(unsafe_code)]` by default (allow only with explicit justification).
- Use `clippy` with `-D warnings` in CI.
- Use `rustfmt` with a pinned toolchain (`rust-toolchain.toml`) for reproducible builds.

## Errors
- Prefer `thiserror` for libraries, `anyhow` for binaries.
- Add context to errors (`.context(...)`) when it clarifies failures.
- Never panic on untrusted input; validate and return errors.
- Avoid `unwrap()`/`expect()` outside tests and obvious invariants.

## Concurrency
- Use `tokio` for async workloads; bound concurrency (semaphores / worker pools).
- Prefer message passing and immutable data.
- Keep locks short; avoid deadlocks with clear ordering.
- Always set timeouts on I/O; avoid unbounded fanout (`join_all`) on attacker-controlled input.

## Security
- Validate inputs and bound sizes at trust boundaries.
- Avoid `Command::new(\"sh\").arg(\"-c\")...` (shell injection).
- Use HTTP clients with timeouts; don’t disable TLS verification.
- Avoid deserializing untrusted data into permissive types; validate lengths/ranges.

## Performance
- Avoid unnecessary clones and allocations; profile before micro-optimizing.
- Prefer `Bytes` for buffers and `Cow` for borrowed/owned duality when appropriate.

## Observability
- Use `tracing` spans per request/job.
- Prefer `try_init()` (avoid panics when initializing tracing in tests).
- Include request-id/correlation-id in spans for request-driven systems.

## References
- `overview.md`
- Snippets: `$CODEX_HOME/snippets/rust/`
- Docs: `../perf/rust-perf.md`, `../security/supply-chain-controls.md`
- Skill: Use skill backend-axum. (when building APIs)
- `$CODEX_HOME/index/pack/style.md`
- `$CODEX_HOME/index/style/rust.md`
