# codex-mcp workflow
You must start with `$CODEX_HOME/plans/workflows/workflow-codex-mcp.md` before executing this workflow.
Purpose: guide work in the Podman-backed MCP stack repo that renders config, prepares runtime state, and launches reference servers for the Codex coding agent.
You must read only the smallest section that resolves the current task, follow the first matching route, and stop broad browsing once the next concrete file or command is clear.

## Repo anchors
- `README.md` for stack contract and runtime layout
- `Makefile` for build/up/verify/doctor targets
- `.env.example` for overridable runtime roots

## Operational focus
- You must keep `.codex/config.toml` rendering deterministic.
- You must keep container image pins, mounts, SSH material, and secret-file contracts explicit.
- You must validate Podman assumptions before changing launcher behavior.
- You must treat `MCP_SECRETS_FILE` as sensitive runtime input; do not bake secrets into repo assets.

## After that, you must check related files
- `$CODEX_HOME/plans/workflows/workflow-codex-mcp.md`
- `$CODEX_HOME/docs/lang/rust.md`
- `$CODEX_HOME/docs/workflows/testing.md`
