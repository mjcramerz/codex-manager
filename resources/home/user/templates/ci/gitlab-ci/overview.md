# GitLab CI templates (overview)
Minimal, reproducible GitLab CI pipelines with security-friendly defaults.

## Inputs
- Destination repository path for this template.
- Exact runtime/image versions and pinning policy.
- Repository-specific values for placeholders, secrets, and host paths.
- Shared include source (`GL_CICD_SHARED_PROJ`) plus protected branch/tag policy.

## Outputs
- `node.yml`: Node.js lint/test/build
- `python.yml`: Python lint/test
- `rust.yml`: Rust fmt/clippy/test
- `security.yml`: optional security audit scaffold
- `github-delivery.yml`: shared include scaffold for GitLab delivery -> GitHub release sync
- `rust-release-delivery.yml`: full Rust release-delivery scaffold (verify/test/sync/release)

## Deterministic usage
1) Copy a template to `.gitlab-ci.yml` or include it from a central repo.
2) Replace image digests (`CHANGE_ME`) with pinned values.
3) Match `rules`, cache keys, and job names to repo policy.
4) Gate delivery jobs to protected `mcr/staging`, protected `mcr/release`, and protected release tags.
5) Wire secrets through CI variables (or BWS) and avoid inline secrets.
6) Run pipeline lint + one MR validation before requiring jobs on protected refs.
7) For Rust release repos, start from `rust-release-delivery.yml` and narrow only what your repo does not use.

## Shared delivery contract (`github-delivery.yml`)
- Include consumer files from `GL_CICD_SHARED_PROJ`: `/github/validate.yml` and `/github/push.yml`.
- Shared contract internals: `/github/version.yml`, `/patches/patches.yml`, `/github/visibility.yml`.
- Keep repo layout: `patches/`, `patches/release/series`, `<repo>/scripts/release/get_version.py`, `<repo>/scripts/release/bump_version.py`.
- Use `rust-release-delivery.yml` when you also need shared `/rustc/verify.yml`, `/rustc/test.yml`, and `/rustc/release-build.yml`.
- Inherit delivery variable contracts from shared includes; set repo-local variable overrides only when behavior differs from shared defaults.
- Default workflow shape: protected tags always run, while protected `mcr/release` branch pipelines should only be created when `GH_RELEASE_PUSH=true`.
- Shared patch helpers currently enforce `patches/release` + `patches/release/series`; keep `PATCH_RELEASE_DIR`/`PATCH_SERIES_FILE` declared for contract visibility.
- Keep mutation order deterministic: `checkout -> true sync -> version bump -> patch apply -> push`.
- In fork mode, sync `origin/github/mcr/main -> github/mcr/main -> mcr/main` before patch checks, and keep patch checks on `mcr/main` only.
- Create and push protected release tags from the tip of `mcr/release` before release sync runs.
- Pair release repos with `.github/workflows/release-*.yml` pinned to shared `release-from-workflow-run.yml` so publish always executes shared security gates.
- Optional GitLab package publishing uses `/gitlab/validate.yml` + `/gitlab/release.yml` and vars `GL_RELEASE_ASSET`, `GL_GROUP_TOP_RELEASE`, `GL_PAT_RELEASE_TOKEN`, `GL_CICD_RUNNER_BUILD`, `GL_CICD_RUNNER_RELEASE`.

## Next steps
1) Copy files into deterministic repository paths.
2) Replace placeholders, pin digests, and set protected vars.
3) Run CI lint and at least one MR pipeline before branch protection changes.

Related:
- `$CODEX_HOME/docs/workflows/gitlab-ci.md`
- `$CODEX_HOME/snippets/ci/gitlab_rules.yml`
- `$CODEX_HOME/snippets/ci/gitlab_delivery_vars.env`
- `$CODEX_HOME/templates/ci/gitlab-ci/rust-release-delivery.yml`
