# codex-manager

`codex-manager` is the source repository for installing, configuring, and maintaining a managed Codex runtime.
It owns the installer, runtime-pack source tree, hook runtime assets, skill catalogs, and runtime plugin marketplace metadata.

## What this repo owns
- Installer and runtime compilation logic in `src/install/**`
- User/runtime config source in `config/usr/**`, `config/vendor/**`, and `config/agents/**`
- Runtime-home source pack in `resources/home/user/**`
- Perl hook runtime source in `resources/hooks/scripts/lib/Codex/Hook/**`
- Runtime skills in `resources/skills/**`
- Plugin skills and marketplace metadata in `resources/plugins/**`

## Key runtime contracts
- `.env` is the source of truth for install root paths.
- `config/usr/apps.toml` drives runtime plugin enablement, agent blocks, shared skill roots, and MCP wiring.
- `resources/skills/metadata.json` drives installer-managed runtime skill groups.
- `resources/plugins/manifest.json` drives the runtime marketplace.
- `resources/home/user/index/manifest.yml` is the routing metadata source for the runtime-home pack.

## Runtime-state boundary
This repository is the source of truth for installable runtime assets only.
Runtime state stays on the installed target and never syncs back into this repo.

Examples of target-only runtime state:
- `$CODEX_HOME/memories/`
- `$CODEX_HOME/sessions/`
- `$CODEX_HOME/shell_snapshots/`
- `$CODEX_HOME/.credentials.json`
- `$CODEX_HOME/history.jsonl`
- `$CODEX_HOME/session_index.jsonl`
- `$CODEX_HOME/version.json`
- `$CODEX_HOME/.personality_migration`

## Adjacent repositories this repo now aligns with
- `debian-preseed-di`
- `cf-aptly-r2`
- `cf-git-cicd-worker`
- `delivery`
- `codex-mcp`

## Useful entrypoints
- Runtime-pack router: `resources/home/user/INDEX.md`
- Runtime memory guidance: consult `$CODEX_HOME/memories/MEMORY.md` only when it exists and the task is repo-aware
- Installer workflow: `resources/home/user/docs/workflows/codex-manager.md`
- MCP stack workflow: `resources/home/user/docs/workflows/codex-mcp.md`
- Cloudflare delivery workflow: `resources/home/user/docs/workflows/cloudflare-delivery.md`

## Validation
For installer/runtime changes, start with the narrowest checks and then run the repo gates:

```bash
python3 -m py_compile src/install/codex_install.py
python3 -m compileall src tests
python3 -m unittest discover -s tests
make preflight
make verify
```

## Install and cleanup notes
- `make install` / `make build-install` materialize runtime config, wrapper state, hook assets, and managed shell exports from this repo.
- `make nuke` / `make uninstall` create a backup first, preserve `CODEX_BACKUP_DIR`, `CODEX_MCP_DIR`, and `CODEX_SQLITE_HOME`, and remove managed shell/profile exports plus runtime paths.
- Managed keyring cleanup during `nuke` / `uninstall` is best-effort: missing `secret-tool` entries no longer abort the filesystem cleanup.
- Persisted `CODEX_*` exports are removed by `nuke` / `uninstall`, but the current shell keeps already-exported values until you refresh it, for example with `exec "$SHELL" -l`.

## Managed MCP auth
- `bearer_token_env_var` is only valid for URL-based MCP servers.
- Stdio / `command` MCP servers must use `env_vars` passed through their wrapper environment instead of bearer-token fields.

## Development notes
- Prefer `rg` / `rg --files` for discovery.
- Prefer `apply_patch` for focused edits.
- Reparse JSON, YAML, and TOML after mutation.
- Keep runtime-only data out of source-controlled docs, templates, and routing assets.
