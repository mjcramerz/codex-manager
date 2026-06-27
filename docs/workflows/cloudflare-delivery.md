# Cloudflare delivery workflow
Start with `$CODEX_HOME/plans/workflows/workflow-cloudflare-delivery.md` before executing this workflow.
Purpose: coordinate Cloudflare Worker repos and the shared GitLab delivery repo without losing the contract between worker code, BWS-loaded secrets, and shared includes.

## Covered repositories
- `cf-git-cicd-worker` — webhook dispatcher Worker, Durable Objects, D1, GitHub Actions dispatch
- `cf-aptly-r2` — R2-backed Aptly publication Worker
- `delivery` — shared GitLab CI/CD templates for Cloudflare, salsa, and OBS workflows

## Workflow rules
- Treat shared delivery includes as contract surfaces, not copy/paste examples.
- Keep Cloudflare API, WAF, custom-domain, and D1 expectations aligned across worker repos and shared templates.
- Keep BWS-only secrets out of repo-tracked config and out of early-evaluated GitLab include/image/tag surfaces.
- When updating worker runtime behavior, reflect the validation flow in the shared delivery guidance the repo actually consumes.

## Validation ladder
1) repo-local lint/type/test commands
2) YAML syntax/shape validation for shared includes or wrapper pipelines
3) contract checks for secret names, routes, and referenced shared template paths

## Related
- `$CODEX_HOME/plans/workflows/workflow-cloudflare-delivery.md`
- `$CODEX_HOME/docs/workflows/gitlab-ci.md`
- `$CODEX_HOME/docs/workflows/ci-cd.md`
