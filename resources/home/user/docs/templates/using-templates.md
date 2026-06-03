# Using templates
Templates are scaffolds you can copy into a repository.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/templates/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Inputs
- Template source path and destination repository path.
- Exact versions/digests for runtimes, images, and actions.
- Repo-specific values for placeholders, secrets, and environment paths.
- Branch/tag and release policy used by your CI system.

## Outputs
- Template files copied with deterministic paths and preserved modes (`cp -a`).
- Placeholder values replaced (`CHANGE_ME`, sample org/version names).
- A runnable baseline that follows the template's own `overview.md`.

## Deterministic flow
1) Copy the template:
   - `cp -a $CODEX_HOME/templates/python/fastapi-app ./myapp`
2) Open the copied template `overview.md` and apply only required edits.
3) Replace placeholders and pin versions/digests before first commit.
4) Ensure lockfiles are present and committed (`Cargo.lock`, `package-lock.json`, etc.).
5) Run the narrowest relevant checks (lint/test/build/dry-run) locally and in CI.

## CI and delivery guardrails
- GitHub Actions baseline: `$CODEX_HOME/templates/ci/github-actions/`.
- GitLab CI baseline: `$CODEX_HOME/templates/ci/gitlab-ci/`.
- Rust release workflow templates:
  - GitHub: `release-build.yml` + `release-publish.yml`
  - GitLab: `rust-release-delivery.yml`
- For GitLab -> GitHub delivery repos:
  - Consumer includes: `/github/validate.yml`, `/github/push.yml` from `GL_CICD_SHARED_PROJ`.
  - Shared internal contract: `/github/version.yml`, `/patches/patches.yml`, `/github/visibility.yml`.
  - Protected release refs: `mcr/staging`, `mcr/release`, and protected release tags.
  - Required mutation order: `checkout -> true sync -> version bump -> patch apply -> push`.
- For GitHub wrapper/shared orchestration, keep repo variables aligned with `$CODEX_HOME/snippets/ci/github_release_vars.env`.

## Next steps
1) Add repo hygiene files from `$CODEX_HOME/templates/common/` (`SECURITY.md`, `CONTRIBUTING.md`, `CODEOWNERS`).
2) Add domain templates you need (`infra/`, `containers/`, `observability/`, `systemd/`, `system/`, `desktop/`, `web/`).
3) Keep only the sections/files your repo actually uses; remove scaffolding you do not adopt.

See also: `overview.md`, `$CODEX_HOME/templates/OVERVIEW.md`, `../workflows/build-an-app.md`, `$CODEX_HOME/index/pack/templates.md`
