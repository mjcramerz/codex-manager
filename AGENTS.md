# AGENTS.md (codex-setup final operating contract)

This file governs `/data/codex/mcp/filesystems/gitlab/source/new/codex-setup`
and all child paths unless a deeper `AGENTS.md` overrides it.

## Authority and scope
- Apply precedence in this order: system -> developer -> user -> this file -> deeper repo instructions.
- Preserve behavior unless the user explicitly requests a change.
- Keep diffs minimal, reviewable, and deterministic.
- Treat unexpected external changes as authoritative user state; never revert without explicit approval.

## Mission for this repository
- This repository is a **fresh-install codex-setup codebase**.
- Do not implement upgrade/uninstall legacy flows.
- Do not introduce helper/preset/profile/watcher/mount management logic.
- Do not add compatibility/legacy fallback paths.
- Fallback behavior is allowed only when the user explicitly requests it; if explicitly requested, the only allowed fallback is **BWS binary download only when `bws` is unavailable**.

## Installation contract (mandatory)
- `.env` is the authoritative source for install root paths.
- Install only into directories designated by `.env`.
- `CODEX_BACKUP_DIR` must exist in `.env` and is used for install backups only.
- No variable from `.env` is exported as a system global automatically.
- `vars.toml` at the repo root is the source for installer-managed global export tables only.
- `[global_variables]` in `vars.toml` drives the managed current-user shell/profile setup only.
- `config/usr/env.toml` is the source for per-launch helper/shim/wrapper exports; keep it separate from host-global exports from `vars.toml` and runtime TOML config merges.
- `config/vendor/mcp.toml` must merge/parse into `/etc/codex/config.toml`.
- `resources/skills/metadata.json` must drive `dependencies.tools` of each target `agents/openai.yaml`:
  - under `$CODEX_SKILLS/**/agents/openai.yaml`
  - under `$CODEX_SYSTEM_DIR/skills/**/agents/openai.yaml` when group path targets system skills
- `resources/instructions/metadata.json` is the source for install-time instruction path rewrites into `$CODEX_HOME/config.toml`.
- `config/usr/apps.toml` is the source for runtime plugin enablement, agent blocks, shared skill roots, and MCP enablement; `resources/plugins/manifest.json` is the plugin manifest source for runtime marketplace generation.
- `config/usr/policy.toml` uses a compact source format under one `[permissions]` table; installer rendering must expand it into the upstream runtime `[permissions.<profile>.{filesystem,network}]` shape.
- During install, `$CODEX_HOME/config.toml` placeholders must be materialized to absolute paths where required.

## MCP policy
- Keep list structures in `config/vendor/mcp.toml` intact (do not silently collapse/remove user lists).
- `context7` must use wrapper command:
  - `/data/codex/mcp/wrappers/mcp-context7-wrapper.sh`
  - `args = []`
- `filesystem` must use wrapper command:
  - `/data/codex/mcp/wrappers/mcp-filesystem-wrapper.sh`
  - `args = []`
- `github_router` must use wrapper command:
  - `/data/codex/mcp/wrappers/mcp-github-router-wrapper.sh`
  - `args = []`
- Audit wrapper source paths from:
  - `<repo>/mcp/wrappers/`
- Pull command/args values from `config/vendor/mcp.toml` when populating tool dependencies.

## Backup and protection rules
- Every install must back up:
  - `$CODEX_HOME`
  - `$CODEX_SQLITE_HOME`
  into `$CODEX_BACKUP_DIR` with a timestamped folder.
- Do not include `$CODEX_SQLITE_HOME` or `$CODEX_MCP_DIR` in uninstall/cleanup deletion flows.
- Repository `make nuke` removes installed runtime state while preserving `CODEX_BACKUP_DIR`, `CODEX_MCP_DIR`, and `CODEX_SQLITE_HOME`.

## Release/tarball policy
- Codex release tarball download source must be GitLab.
- Enforce HTTPS and fail closed on invalid URL/sha checks.

## Security and reliability baseline
- Validate and bound all inputs.
- Use bounded retries/timeouts for network and I/O.
- Block path traversal and unsafe archive extraction.
- Never log secrets or dump full environment values.
- Avoid destructive commands unless explicitly requested and acknowledged.

## Tooling and editing discipline
- Prefer `rg`/`rg --files` for search/discovery.
- Prefer `apply_patch` for small single-file edits.
- Use scripts for repeated multi-file transformations.
- Use explicit, deterministic commands and report exact paths touched.

## Verification gates
Run these after installer changes:
- `python3 -m py_compile src/install/codex_install.py`
- `make preflight`
- `make verify`

If real install is requested, run `make install` and report any permission boundary exactly.

## Output expectations
- Return: Summary -> Tests -> Risks/TODOs -> Next steps.
- Include concrete file references with line numbers when reporting changes.
- State assumptions explicitly when behavior depends on environment permissions or credentials.
