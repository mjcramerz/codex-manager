# Plan

Use this plan when following `$CODEX_HOME/docs/workflows/codex-repo.md`.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/workflows/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Inputs
- `$CODEX_HOME/docs/workflows/codex-repo.md`
- `$CODEX_HOME/index/core/codex-repo.md`
- Current Codex source scope and affected directories
- Upstream schema: `https://raw.githubusercontent.com/openai/codex/refs/heads/main/codex-rs/core/config.schema.json`
- Upstream bundled models: `https://raw.githubusercontent.com/openai/codex/main/codex-rs/core/models.json`

## Scope
- In: source-to-pack coverage alignment for tooling, workflows, and web-stack guidance.
- In: config schema parity (`$CODEX_HOME/config.toml`, `/etc/codex/config.toml`) and model-catalog bootstrap (`$CODEX_HOME/.models/model_catalog.json`).
- Out: unrelated repository changes without coverage impact.

- For API/protocol surfaces, define contract versioning, timeout/retry ceilings, and idempotency/error-model expectations.

## Action items
[ ] Route through `$CODEX_HOME/index/core/codex-repo.md`, then execute `$CODEX_HOME/docs/workflows/codex-repo.md`.
[ ] Inventory source workflows, release paths, and technologies tied to the requested surface area.
[ ] Map findings to pack assets and mark missing, stale, or conflicting coverage.
[ ] Apply focused updates with concrete commands, acceptance checks, and risk notes (including config/schema parity keys).
[ ] Refresh local model catalog (`$CODEX_HOME/.models/model_catalog.json`) from upstream `codex-rs/core/models.json` when required.
[ ] Regenerate routing artifacts only when entrypoints change, then run verification.
[ ] Record residual source-to-pack gaps with owner and follow-up action.

## Testing and validation
- Run the narrowest syntax/quality checks for touched assets.
- Run the active worktree’s broader validation command set when the change spans multiple runtime surfaces.
- Validate TOML and JSON syntax for config/catalog changes before full verify.
- Accept only if mapped source paths exist and each updated pack artifact has verification evidence.

## Security checkpoints
- Keep source-to-pack mapping read-only until update scope is confirmed.
- Record any required permission/secret exception with owner, reason, and expiry.

## Testing checkpoints
- Define fast-path and deep-path checks with explicit pass criteria before edits.
- Re-run impacted checks after major mapping updates and before handoff.

## Deployment checkpoints
- Land pack alignment updates before related source release cuts when possible.
- Record rollback commit reference and post-sync owner in handoff notes.

## Multi-agent handoff
- Coordinator hands off scope, target entrypoint, and stop condition.
- Executor reports touched files, commands, evidence, blockers, and next action.

## Risks and edge cases
- Coverage drift between source workflows and pack documentation.
- Incomplete CI/release mapping leading to stale or misleading guidance.

## Open questions
- None.
