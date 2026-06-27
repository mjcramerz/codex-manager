# Codex Operator Docs
Purpose: provide the installed operator-doc source that is synced into `/data/codex/docs`.

## Use this directory when
- you need wrapper, login, token, or installation commands
- you need the host-side procedure for `make install`, `make runtime`, or `make nuke`
- you need the exact lookup-file locations under `/data/codex/lookup/`

## Primary docs
- `wrappers.md` — wrapper commands and when to use them
- `security/overview.md` — secrets, auth, and token rotation
- `security/secrets.md` — `secrets.toml`, `auth.toml`, `codex-login`, and `codex-mcp-token`
- `workflows/overview.md` — install/runtime workflow index
- `workflows/codex-manager.md` — install, runtime refresh, vars, and nuke commands
