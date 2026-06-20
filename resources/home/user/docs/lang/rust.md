# Rust
Purpose: guide Rust and Cargo work in Codex source repos, release flows, and validation-heavy runtime integrations.

## Use this guide when
- working in a Cargo workspace
- mapping source-repo commands into pack docs or CI templates
- reviewing release, lint, or packaging expectations for Rust projects

## Baseline
- Prefer pinned toolchains via `rust-toolchain.toml`.
- Keep `cargo fmt --check`, `cargo clippy -- -D warnings`, and targeted tests in the default validation path.
- Use `cargo --locked` in CI and release flows when a lockfile exists.
- Keep release packaging and schema/config regeneration steps explicit in docs and plans.

## Validation ladder
1. `cargo fmt --check`
2. `cargo clippy --workspace --all-targets -- -D warnings`
3. targeted `cargo test` or `cargo nextest`
4. release/package checks only when the task touches packaging or publishing

## Related
- `$CODEX_HOME/docs/style/rust.md`
- `$CODEX_HOME/docs/workflows/codex-repo.md`
- `$CODEX_HOME/docs/workflows/codex-mcp.md`
- `$CODEX_HOME/index/domains/lang/rust.md`
