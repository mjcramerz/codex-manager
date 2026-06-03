# Containers overview
This pack treats containers as a first-class, reproducible dev and test environment.


## Contents
<!-- BEGIN:contents -->
- `$CODEX_HOME/docs/containers/buildx.md` — Docker Buildx
- `$CODEX_HOME/docs/containers/dev-containers.md` — Dev containers (devlab / codelab)
- `$CODEX_HOME/docs/containers/docker-compose.md` — Docker Compose
- `$CODEX_HOME/docs/containers/dockerfile.md` — Dockerfile guidance
- `$CODEX_HOME/docs/containers/podman.md` — Podman
- `$CODEX_HOME/docs/containers/rootless-docker.md` — Rootless Docker
<!-- END:contents -->


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


Goals:
- default to least privilege (rootless engine when possible; non-root containers)
- make network access explicit and configurable (online vs offline)
- keep builds deterministic (pinned toolchains/images; lockfiles; no “latest”)

## Pick an engine
- **Rootless Docker**: good default on Linux for developer workflows when available.
- **Rootful Docker**: use only when you explicitly need it (system-level integration, privileged workloads).
- **Podman**: rootless by default; great for local dev and CI; compatible with Dockerfiles for most projects.

## Build tools (Docker + Podman)
- **Docker Buildx (BuildKit)**: preferred for multi-arch and cache-aware builds.
- **Buildah**: daemonless image builds (often paired with Podman); solid choice for rootless workflows.

## Engine + user matrix (full coverage)
- **Docker rootless + non-root container**: default for least privilege.
- **Docker rootful + non-root container**: use when rootless can’t meet requirements.
- **Docker rootful + root container**: only when you must install packages or run privileged tooling.
- **Podman rootless + non-root container**: default for Podman.
- **Podman rootful + root container**: use only when rootless Podman is insufficient.

## Dev containers (devlab / codelab)
Use the dev container template when you need a reproducible coding environment with common tools installed.
See `dev-containers.md` and the devlab/codelab template for Docker + Podman examples.

## Baseline container hygiene
- Run the service process as non-root (`USER` in Dockerfile).
- Avoid `--privileged`, `--cap-add=ALL`, and mounting the Docker socket unless explicitly required and reviewed.
- Do not bake secrets into images; use runtime env/secret mounts.
- Prefer small images; keep layers cache-friendly.
- For bind-mounted host paths, match container UID/GID to the engine user (`id -u` / `id -g`).
- For Podman rootless, always use `compose.podman.override.yml` with `userns_mode: keep-id` for bind mounts so host ownership matches the engine user.
- Use `rootless_env.sh --dotenv > .env` (or `make env` when available) to populate UID/GID vars.

## Network access: make it explicit
Many tasks (tests, lint, builds) do not need internet access once deps are present.

Patterns:
- **Disable network for runtime**: `docker run --network=none ...`
- **Disable network for build steps** (where supported): `docker build --network=none ...`
- **Compose offline override**: set `network_mode: "none"` for the service.

If network is required:
- Keep the default (online) Compose network enabled.
- Pass proxy env vars explicitly when your environment requires it (see template `.env.example`).
- Prefer allowlists for outbound destinations when implementing SSRF-sensitive features.

## Rootless connectivity baseline (internet access)
For rootless Docker/Podman, internet access should work on the default bridge network. If it doesn’t:
- verify you are targeting the intended daemon (`docker context ls`)
- confirm the rootless network driver is available (`slirp4netns`/`pasta` for Podman, rootlesskit for Docker)
- check DNS inside a container and add explicit DNS only if required

See `rootless-docker.md` for troubleshooting guidance.

## Docker contexts (rootless vs rootful)
Use contexts so the same `docker` CLI can target different daemons:
- `docker context ls`
- `docker context use <name>`

Context names are host-specific; this pack’s examples use `rootless` and `rootful` when available.

- Template: `$CODEX_HOME/templates/containers/docker-compose-skeleton/` (includes Podman keep-id override)
- Template: `$CODEX_HOME/templates/containers/dockerfile-skeleton/`
- Template: `$CODEX_HOME/templates/containers/devlab-codelab-skeleton/`
- Snippets: `$CODEX_HOME/snippets/containers/`
- Skill: Use skill infra-containers.

See also:
- `dev-containers.md`
- `rootless-docker.md`
- `docker-compose.md`
- `dockerfile.md`
- `buildx.md`
- `podman.md`
- `../workflows/containers.md`
- `$CODEX_HOME/index/domains/infra/containers.md`
- `$CODEX_HOME/index/pack/templates.md`
- `$CODEX_HOME/index/pack/snippets.md`
