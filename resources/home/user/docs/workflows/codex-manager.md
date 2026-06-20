# codex-manager workflow
Start with `$CODEX_HOME/plans/workflows/workflow-codex-manager.md` before executing this workflow.
Purpose: guide work in the Codex installer/runtime-pack source repo that owns install flow, home sync, hooks, runtime config, skills, and plugin marketplace content.

## Primary surfaces
- Installer: `src/install/**`
- Runtime config source: `config/usr/**`, `config/vendor/**`, `config/agents/**`
- Runtime-home source pack: `resources/home/user/**`
- Hook runtime source: `resources/hooks/scripts/lib/Codex/Hook/**`
- Skills and plugin marketplace: `resources/skills/**`, `resources/plugins/**`

## Cross-repo alignment
- Check `codex-mcp` when MCP launcher/runtime expectations change.
- Check `delivery` when CI templates or Cloudflare deploy expectations change.
- Check `cf-git-cicd-worker` and `cf-aptly-r2` when Cloudflare-oriented skills or workflows are refreshed.

## State boundary
- Runtime home is source-to-target only; runtime state never syncs back into this repo.
- Runtime-only examples: `$CODEX_HOME/memories/`, `$CODEX_HOME/sessions/`, `$CODEX_HOME/shell_snapshots/`, `$CODEX_HOME/.credentials.json`, `$CODEX_HOME/history.jsonl`, `$CODEX_HOME/session_index.jsonl`, `$CODEX_HOME/version.json`, and `$CODEX_HOME/.personality_migration`.

## Install and nuke checkpoints
- Keep `install`, `update`, `nuke`, and `uninstall` idempotent for already-applied or already-removed runtime state.
- `nuke` / `uninstall` must remove managed shell/profile exports for future sessions and clearly note that the current shell keeps already-exported `CODEX_*` values until refresh.
- Managed `secret-tool` cleanup during `nuke` / `uninstall` is best-effort; missing keyring entries must not block filesystem cleanup.
- `bearer_token_env_var` is URL-only MCP config. Stdio / `command` servers must use `env_vars` instead.

## Validation ladder
1) syntax/parse checks for touched files
2) focused unit tests for changed installer logic
3) runtime-pack docs/skill contract tests when catalogs changed
4) broader repo validation only when scope crosses installer/runtime surfaces

## Related
- `$CODEX_HOME/plans/workflows/workflow-codex-manager.md`
- `$CODEX_HOME/docs/workflows/runtime-pack-maintenance.md`
- `$CODEX_HOME/docs/architecture.md`
