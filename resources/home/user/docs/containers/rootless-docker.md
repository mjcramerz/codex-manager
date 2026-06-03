# Rootless Docker
Rootless Docker runs the Docker daemon without root privileges. This reduces host risk and is a strong default for development.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/containers/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## How to connect (common patterns)
### Same user (default rootless socket)
For the user running the rootless daemon:
- `DOCKER_HOST=unix:///run/user/<uid>/docker.sock`

### Shared proxy socket (optional)
Some host setups expose a group-readable proxy socket (example path):
- `DOCKER_HOST=unix:///var/run/docker-rootless/<user>/docker.sock`

This lets non-daemon users access the rootless daemon via group membership (treat this as a privilege boundary).

### Docker contexts
Prefer contexts over exporting `DOCKER_HOST`:
- `docker context ls`
- `docker context use rootless`

## Known limitations (plan accordingly)
- Low ports: binding `<1024` may require additional host configuration; prefer higher ports (e.g., 3000/8000/8080).
- Networking modes: “host” networking and some advanced modes may not work as on rootful Docker.
- Privileged workloads: rootless is intentionally restrictive; avoid `--privileged` and assume reduced kernel access.

## Root vs non-root containers
- Default to non-root (`USER` in Dockerfile, `user:` in compose).
- Root inside a rootless daemon is still unprivileged on the host.
- Use rootful Docker only when you truly need host-level capabilities.

## UID/GID and bind mounts
- When bind-mounting host paths, set the container `user:` to the engine UID/GID (`id -u` / `id -g`). Use `rootless_env.sh --dotenv > .env` when provided.

## Recommended defaults in templates
- Dockerfiles run the app as a non-root user.
- Compose templates include an “offline” override to disable network.

## Network troubleshooting (rootless)
If containers do not have outbound internet access:
- Verify you are targeting the rootless daemon (`docker context ls`).
- Confirm the rootless network stack is installed/enabled (rootlesskit + slirp4netns).
- Check DNS inside a container; add explicit DNS only if required by your environment.
- Avoid `network_mode: host` with rootless daemons; use the default bridge network.

See also:
- `overview.md`
- `docker-compose.md`
- `dockerfile.md`
- `podman.md`
- `../workflows/containers.md`
- `$CODEX_HOME/index/domains/infra/containers.md`
