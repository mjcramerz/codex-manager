# Wrapper Commands
Purpose: document the installed wrapper commands under `/data/bin`.

## Commands
- `codex` — main Codex entrypoint; when managed MCP secrets are configured, this wrapper injects them before launching the real binary.
- `codex-login` — logs into Codex using a hidden prompt, one-shot `CODEX_ACCESS_TOKEN`, or a stored account from `/data/codex/lookup/auth.toml`.
- `codex-mcp-token` — stores or rotates one enabled MCP token from `/data/codex/lookup/secrets.toml`.
- `codex-schema-newest` — prints the newest available schema snapshot.
- `codex-schema-diff` — compares the installed schema against the rendered runtime config.

## Notes
- Old `codex-s` aliases are removed; use `codex` directly.
- Wrapper lookup files live under `/data/codex/lookup/`.
- Wrapper helpers live under `/data/codex/share/helpers/`.
