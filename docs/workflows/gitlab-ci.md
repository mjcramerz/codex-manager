# GitLab CI/CD workflow

Start with `$CODEX_HOME/plans/workflows/workflow-gitlab-ci.md` before executing this workflow.
Purpose: provide GitLab-specific CI guidance with security and reproducibility defaults.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/workflows/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Direct routing
- For cross-platform CI policy, use `ci-cd.md`.
- For Cloudflare Worker plus shared delivery repos, use `cloudflare-delivery.md`.
- For release tagging and publish sequencing, use `release.md`.

## Baseline design
- Define `stages` explicitly and keep them small: `verify`, `test`, `security`, `release`.
- Use `workflow: rules` to avoid duplicate pipelines.
- Prefer per-job `rules` over `only/except`.
- Use `needs` to reduce critical-path time.
- Set `interruptible: true` and add `resource_group` for jobs that must serialize.

## Shared delivery include pattern
- Treat shared delivery includes as a contract owned by the `delivery` repository.
- Keep consumer `.gitlab-ci.yml` files thin and explicit about protected refs, runner classes, and variable overrides.
- For GitLab-to-GitHub publishing, include the shared delivery files through `GL_CICD_SHARED_PROJ` and avoid duplicating the internal shared include graph unless intentionally forking behavior.
- Keep mirror-sync, version bump, patch application, and publish order deterministic.

## Reproducibility
- Pin container images by digest; avoid `:latest`.
- Pin language toolchains and use lockfiles.
- Use deterministic install commands (`cargo --locked`, `npm ci`, `pip --require-hashes` where feasible).

## Security checkpoints
- Keep release jobs restricted to protected branches/tags and protected variables.
- Pin executor images by digest and review any privileged capability change.
- Ensure `rules` block deploy and secret-consuming jobs on untrusted merge request pipelines.

## See also
- `ci-cd.md`
- `cloudflare-delivery.md`
- `release.md`
- `repo-ops.md`
