# Cloudflare delivery workflow
You must start with `$CODEX_HOME/plans/workflows/workflow-cloudflare-delivery.md` before executing this workflow.
Purpose: coordinate Cloudflare Worker repos and the shared GitLab delivery repo without losing the contract between worker code, BWS-loaded secrets, and shared includes for the Codex coding agent.
You must read only the smallest section that resolves the current task, follow the first matching route, and stop broad browsing once the next concrete file or command is clear.

## Covered repositories
- `cf-git-cicd-worker` — webhook dispatcher Worker, Durable Objects, D1, GitHub Actions dispatch
- `cf-aptly-r2` — R2-backed Aptly publication Worker
- `delivery` — shared GitLab CI/CD templates for Cloudflare, salsa, and OBS workflows

## Workflow rules
- You must treat shared delivery includes as contract surfaces, not copy/paste examples.
- You must keep Cloudflare API, WAF, custom-domain, and D1 expectations aligned across worker repos and shared templates.
- You must keep BWS-only secrets out of repo-tracked config and out of early-evaluated GitLab include/image/tag surfaces.
- When updating worker runtime behavior, reflect the validation flow in the shared delivery guidance the repo actually consumes.

## Validation ladder
1) repo-local lint/type/test commands
2) YAML syntax/shape validation for shared includes or wrapper pipelines
3) contract checks for secret names, routes, and referenced shared template paths

## After that, you must check related files
- `$CODEX_HOME/plans/workflows/workflow-cloudflare-delivery.md`
- `$CODEX_HOME/docs/workflows/gitlab-ci.md`
- `$CODEX_HOME/docs/workflows/ci-cd.md`
