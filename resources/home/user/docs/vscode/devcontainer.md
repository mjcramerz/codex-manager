# VS Code devcontainers
Guidance for reproducible, safe devcontainers (`.devcontainer/`).


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/vscode/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Core files
- `.devcontainer/devcontainer.json`
- `.devcontainer/Dockerfile` or an image reference
- Optional: `.devcontainer/docker-compose.yml`

## Recommended defaults
- Pin base images (tag + digest) and toolchains.
- Run as non-root (`remoteUser`) where possible.
- Keep secrets out of images; inject via env or secret stores.
- Make network usage explicit and documented.
- If bind-mounting host paths, align the container user to the engine UID/GID; for Podman rootless, require `keep-id` where supported.

## Engine support
- Devcontainers can run on Docker or Podman (if your tooling supports it).
- If using Podman, verify the devcontainer CLI/extension is configured to target Podman.

## Snippet
- `$CODEX_HOME/snippets/vscode/devcontainer.json`

See also:
- `overview.md`
- `../containers/overview.md`
- `../containers/dev-containers.md`
- `../containers/docker-compose.md`
- `../containers/rootless-docker.md`
- `$CODEX_HOME/templates/containers/devlab-codelab-skeleton/`
- `$CODEX_HOME/templates/containers/docker-compose-skeleton/`
- `$CODEX_HOME/index/domains/vscode/guidance.md`
