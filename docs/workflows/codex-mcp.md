# codex-mcp workflow
Start with `$CODEX_HOME/plans/workflows/workflow-codex-mcp.md` before executing this workflow.
Purpose: guide work in the Podman-backed MCP stack repo that renders config, prepares runtime state, and launches reference servers.

## Repo anchors
- `README.md` for stack contract and runtime layout
- `Makefile` for build/up/verify/doctor targets
- `.env.example` for overridable runtime roots

## Operational focus
- Keep `.codex/config.toml` rendering deterministic.
- Keep container image pins, mounts, SSH material, and secret-file contracts explicit.
- Validate Podman assumptions before changing launcher behavior.
- Treat `MCP_SECRETS_FILE` as sensitive runtime input; do not bake secrets into repo assets.

## Related
- `$CODEX_HOME/plans/workflows/workflow-codex-mcp.md`
- `$CODEX_HOME/docs/lang/rust.md`
- `$CODEX_HOME/docs/workflows/testing.md`
