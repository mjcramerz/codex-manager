# codex-manager workflow
Purpose: guide work in the Codex installer/runtime-pack source repo that owns install flow, home sync, hooks, runtime config, skills, and plugin marketplace content for the Codex coding agent.
You must read only the smallest section that resolves the current task, follow the first matching route, and stop broad browsing once the next concrete file or command is clear.

You must start with `$CODEX_HOME/plans/workflows/workflow-codex-manager.md` before executing this workflow.

## Primary surfaces
- Compiled runtime home config: `$CODEX_HOME/config.toml`
- Compiled agent and system config: `$CODEX_AGENTS/*.toml`, `/etc/codex/config.toml`, `/etc/codex/requirements.toml`
- Runtime-home pack: `$CODEX_HOME/**`
- Hook runtime source: `$CODEX_HOME/hooks/scripts/lib/Codex/Hook/**`
- Skills and plugin marketplace: `$CODEX_HOME/.agents/skills/**`, `$CODEX_HOME/plugins/cache/**`, `$CODEX_HOME/.agents/plugins/marketplace.json`

## Cross-repo alignment
- You must check `codex-mcp` when MCP launcher/runtime expectations change.
- You must check `delivery` when CI templates or Cloudflare deploy expectations change.
- You must check `cf-git-cicd-worker` and `cf-aptly-r2` when Cloudflare-oriented skills or workflows are refreshed.

## State boundary
- Runtime home is source-to-target only; runtime state never syncs back into this repo.
- You must keep guidance centered on installed config, docs, plans, skills, templates, snippets, and plugin marketplace surfaces.
- You must route memory-specific guidance through `$CODEX_HOME/memories/` and the matching workflow entrypoints.

## Install and nuke checkpoints
- You must keep `install`, `runtime`, `runtime-home`, `runtime-skills`, `runtime-instructions`, and `nuke` idempotent for already-applied or already-removed runtime state.
- `make install` must act as both fresh install and in-place upgrade, without requiring a separate upgrade command.
- `nuke` must remove managed shell/profile exports for future sessions and clearly note that the current shell keeps already-exported `CODEX_*` values until refresh.
- Managed `secret-tool` cleanup during `nuke` is best-effort; missing keyring entries must not block filesystem cleanup.
- `bearer_token_env_var` is URL-only MCP config. Stdio / `command` servers must use `env_vars` instead.

## Validation ladder
1) syntax/parse checks for touched files
2) focused unit tests for changed installer logic
3) runtime-pack docs/skill contract tests when catalogs changed
4) broader repo validation only when scope crosses installer/runtime surfaces

## After that, you must check related files
- `$CODEX_HOME/plans/workflows/workflow-codex-manager.md`
- `$CODEX_HOME/docs/workflows/runtime-pack-maintenance.md`
- `$CODEX_HOME/docs/architecture.md`
