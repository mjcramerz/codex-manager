# Workflow catalog
Purpose: map recurring task types to operational playbooks and help the agent choose one workflow before editing.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Workflow catalog
<!-- BEGIN:contents -->
- `$CODEX_HOME/docs/workflows/runtime-pack-maintenance.md` — Runtime-pack maintenance workflow
- `$CODEX_HOME/docs/workflows/codex-manager.md` — codex-manager installer/runtime workflow
- `$CODEX_HOME/docs/workflows/codex-mcp.md` — codex-mcp stack workflow
- `$CODEX_HOME/docs/workflows/cloudflare-delivery.md` — Cloudflare + GitLab delivery workflow
- `$CODEX_HOME/docs/workflows/debian-preseed.md` — Debian preseed workflow
- `$CODEX_HOME/docs/workflows/ci-cd.md` — CI/CD workflow
- `$CODEX_HOME/docs/workflows/gitlab-ci.md` — GitLab CI/CD workflow
- `$CODEX_HOME/docs/workflows/testing.md` — Testing workflow
- `$CODEX_HOME/docs/workflows/repo-ops.md` — Repo operations workflow
- `$CODEX_HOME/docs/workflows/codex-repo.md` — Codex source repository workflow
<!-- END:contents -->

## Selection guide
- Runtime-pack source changes -> `runtime-pack-maintenance.md`
- Installer/home-sync/hooks/config work -> `codex-manager.md`
- Podman MCP stack generation/launch -> `codex-mcp.md`
- Cloudflare Worker plus delivery-template repos -> `cloudflare-delivery.md`
- Debian installer trees and unattended install contracts -> `debian-preseed.md`

## Maintenance rules
- Every workflow added here should have a corresponding plan under `$CODEX_HOME/plans/workflows/` when the execution path is non-trivial.
- Prefer repo-grounded guidance for the named adjacent repositories.
