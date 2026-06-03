# GitLab CI/CD workflow

Start with `$CODEX_HOME/plans/workflows/workflow-gitlab-ci.md` before executing this workflow.
Purpose: provide GitLab-specific CI guidance with security and reproducibility defaults.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/workflows/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Plan
- Start from the linked workflow plan template above, then tailor scope, constraints, and validation commands before editing.
- Keep the plan updated as execution progresses, including risk and rollback notes for any sensitive change.

## Direct routing
- For cross-platform CI policy, use `ci-cd.md`.
- For release tagging and publish sequencing, use `release.md`.

## Baseline design
- Define `stages` explicitly and keep them small: `verify`, `test`, `security`, `release`.
- Use `workflow: rules` to avoid duplicate pipelines.
- Align top-level `workflow: rules` with protected `mcr/staging`, protected `mcr/release`, and protected release tags; gate release builds on tags that point to the tip of `mcr/release`.
- Prefer per-job `rules` over `only/except`.
- Use `needs` to reduce critical-path time.
- Set `interruptible: true` and add `resource_group` for jobs that must serialize.

## Shared delivery include pattern
For GitLab-to-GitHub publishing, include shared delivery files via `GL_CICD_SHARED_PROJ`:
  - `/github/validate.yml`
  - `/github/push.yml`
- Treat both include paths above as mandatory for any GitLab-project `.gitlab-ci.yml` in this pack.
- Shared GitHub includes pull `/github/version.yml`, `/patches/patches.yml`, and `/github/visibility.yml` internally; consumer repos should not duplicate those includes unless intentionally overriding shared behavior.
- For GitLab Generic Package release assets, add:
  - `/gitlab/validate.yml`
  - `/gitlab/release.yml`
  - one stack build include (for example `/rustc/release-build.yml`)
- Keep rules aligned with delivery expectations:
  - block `main`/`mcr/main` for sync jobs
  - allow protected `mcr/release`
  - allow protected release tags
- Keep tracked mirror branches read-only in fork mode (`github/mcr/main`, `github/mcr/staging`); worker sync should not mutate these refs manually.
- In fork mode, synchronize `origin/github/mcr/main -> github/mcr/main -> mcr/main` before release patch checks.
- In fork mode, keep release patch checks on `mcr/main` only before promoting `mcr/staging` and `mcr/release`.
- Keep sync mutation order deterministic: `checkout -> true sync -> version bump -> patch apply -> push` (for the release ref).
- Keep variable contracts aligned with `$CODEX_HOME/snippets/ci/gitlab_delivery_vars.env`.
- Keep paired `.github/workflows/release-*.yml` callers pinned to shared `release-from-workflow-run.yml`; shared workflow performs release security gates before publish.
- Prefer shared include defaults for delivery variables; declare repo-local overrides only when intentionally diverging from shared behavior.
- For GitLab package publishing, keep `GL_RELEASE_ASSET`, `GL_GROUP_TOP_RELEASE`, `GL_PAT_RELEASE_TOKEN`, `GL_CICD_RUNNER_BUILD`, and `GL_CICD_RUNNER_RELEASE` explicit and protected.
- Shared patch helpers currently enforce `patches/release` + `patches/release/series`; keep `PATCH_RELEASE_DIR` and `PATCH_SERIES_FILE` declared for compatibility/visibility.

## Reproducibility
- Pin container images by digest; avoid `:latest`.
- Pin language toolchains and use lockfiles.
- Use deterministic install commands (`cargo --locked`, `npm ci`, `pip --require-hashes` where feasible).
- Keep `GIT_DEPTH` small for speed and increase only when needed.

## Security
- Avoid `privileged` and Docker socket mounts; prefer rootless or Kaniko.
- Use minimal job permissions and least-privilege tokens.
- Add timeouts and bounded retries (`timeout`, `retry`).
- Never echo secrets; avoid dumping environment variables.

## Secrets management
- Store secrets as masked/protected CI variables.
- Prefer a secrets manager (e.g., Bitwarden Secrets Manager).
- Use explicit BWS env names in CI contracts: `BWS_ACCESS_TOKEN` and `BWS_PROJECT_ID`.

## Templates
- GitLab CI templates: `$CODEX_HOME/templates/ci/gitlab-ci/`
- Minimal rules snippet: `$CODEX_HOME/snippets/ci/gitlab_rules.yml`
- GitLab delivery include template: `$CODEX_HOME/templates/ci/gitlab-ci/github-delivery.yml`
- GitLab Rust release delivery template: `$CODEX_HOME/templates/ci/gitlab-ci/rust-release-delivery.yml`

## Security checkpoints
- Keep release jobs restricted to protected branches/tags and protected variables.
- Pin executor images by digest and review any privileged capability change.
- Ensure `rules` block deploy and secret-consuming jobs on untrusted merge request pipelines.

## Testing checkpoints
- Validate `.gitlab-ci.yml` through CI lint before merge and after major `include`/`rules` edits.
- Run stage-level smoke checks to confirm `needs` graph and artifact passing behavior.
- Track flaky jobs with retry rationale; do not use retries to mask real failures.

## Deployment checkpoints
- Use explicit `environment` jobs with approvals (`when: manual`) for production promotion.
- Promote artifacts via `needs:artifacts` from verified build stages; avoid rebuilds in deploy jobs.
- Provide rollback job definitions per environment using the previous artifact version.

## Multi-agent handoff
- Pipeline author shares stage graph, `rules` intent, and affected includes with reviewers.
- Security reviewer confirms protected-variable scope and runner trust assumptions.
- Deploy operator receives manual-gate job names, target environment, and rollback job reference.
See also:
- `overview.md`
- `ci-cd.md`
- `github-actions.md`
- `../security/secrets.md`
- Use skill `ci-gitlab-cicd`.
- Use skill `repo-ops`.
- Use skill `secops-supply-chain`.
- `$CODEX_HOME/index/pack/workflows.md`
- `$CODEX_HOME/index/core/ci-cd.md`
