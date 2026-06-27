# Rootless Docker
Purpose: document the practical constraints and default-safe usage of a rootless Docker daemon.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/containers/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Default posture
- Prefer rootless Docker for developer workflows.
- Keep containers non-root unless there is a concrete bootstrap need.
- Prefer Docker contexts over ad-hoc `DOCKER_HOST` exports.

## What to check first
- `docker context ls`
- the active daemon socket path
- whether bind-mounted files will stay owned by the invoking user
- whether the workload actually needs rootful-only networking or privilege

## Common limitations
- Low ports and some host-network expectations may need extra host setup.
- Privileged workloads remain intentionally constrained.
- Debugging should start with daemon selection and network/DNS inspection, not with switching to rootful Docker by default.

## Related
- `overview.md`
- `dev-containers.md`
- `docker-compose.md`
- `$CODEX_HOME/docs/workflows/containers.md`
