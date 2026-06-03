# Dev containers (devlab / codelab)
Reproducible dev containers for Codex coding agents and local development workflows.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/containers/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## When to use
- You need a consistent dev environment across machines or CI.
- You want a codelab/devlab container with common tooling installed.
- You want rootless-by-default with an explicit root override.

## Engines and modes (full coverage)
- **Docker rootless**: `docker context use rootless` (default for least privilege).
- **Docker rootful**: `docker context use rootful` (only when you need it).
- **Podman rootless**: `podman ...` as your user (default for Podman).
- **Podman rootful**: `sudo podman ...` or a rootful service when required.

## Container user: non-root vs root
- Default is non-root (`user` in compose + `USER` in Dockerfile).
- Use a root override only when you must install packages or run privileged tooling.
- Root inside a **rootless** engine is still unprivileged on the host.

## Tooling baseline (common dev tools)
The devlab/codelab template installs a baseline set of tools:
- git, curl/wget, SSH client, CA certs
- build-essential, pkg-config, cmake, ninja
- Python 3 + pip + venv
- Node.js + npm
- Go + Rust (cargo)
- jq, ripgrep, fd-find, zip/unzip

If you need slimmer images or newer toolchains, replace the package list and pin versions explicitly.

## UID/GID and ports
- For rootless engines, set `DEV_UID`/`DEV_GID` to the user running the engine (`id -u` / `id -g`) so file ownership matches.
- Tip: from the copied template root, run `bash rootless_env.sh --dotenv > .env` (or `make env` when the template includes it).
- Start from `.env.example` in the template and fill UID/GID values as needed.
- The devlab/codelab template maps `DEV_PORT` (default 8080) to container port 8080.
- For Podman, **always** use `compose.podman.override.yml` (`userns_mode: keep-id`) when bind-mounting host paths.
- If you must run as container root, use `compose.rootful.override.yml` (UID/GID 0:0).

## Template
Use the devlab/codelab template:
- `$CODEX_HOME/templates/containers/devlab-codelab-skeleton/`

It provides:
- `compose.yml` for online dev
- `compose.offline.override.yml` for offline runtime
- `compose.rootful.override.yml` to run as root inside the container
- `compose.podman.override.yml` with `userns_mode: keep-id`
- `.env.example` with UID/GID and proxy placeholders

## Example commands
Docker (rootless):
```bash
docker context use rootless
docker compose -f compose.yml up --build
```

Docker (rootful, container root):
```bash
docker context use rootful
docker compose -f compose.yml -f compose.rootful.override.yml up --build
```

Podman (rootless):
```bash
podman compose -f compose.yml -f compose.podman.override.yml up --build
```

Podman (rootful, container root):
```bash
sudo podman compose -f compose.yml -f compose.rootful.override.yml up --build
```

Offline runtime (no container network):
```bash
docker compose -f compose.yml -f compose.offline.override.yml up --build
# or: podman compose -f compose.yml -f compose.offline.override.yml up --build
```

## Notes
- For Podman rootless, require `compose.podman.override.yml` and ensure UID/GID match the engine user.
- Avoid privileged containers and Docker socket mounts unless explicitly required and reviewed.
- If `podman compose` is unavailable, use `podman-compose` with the same files.

See also:
- `overview.md`
- `podman.md`
- `docker-compose.md`
- `dockerfile.md`
- `../workflows/containers.md`
- `$CODEX_HOME/templates/containers/devlab-codelab-skeleton/`
