# CI/CD workflow

Start with `$CODEX_HOME/plans/workflows/workflow-ci-cd.md` before executing this workflow.
Purpose: provide canonical CI/CD guidance for this pack.


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
- If you are defining cross-platform CI policy, start here.
- If you are editing GitHub workflows/wrappers, route to `github-actions.md`.
- If you are editing `.gitlab-ci.yml` or delivery includes, route to `gitlab-ci.md`.
- If you are preparing release tagging/publish steps, route to `release.md`.

## CI gates (recommended)
1) Format
2) Lint/static analysis
3) Unit tests
4) Integration tests (as appropriate)
5) Dependency vulnerability audit
6) Secret scanning (baseline)
7) SBOM generation (release builds)
8) Artifact signing (org policy)

## Workflow design
- **Fast path** on every PR/push: fmt + lint + unit tests.
- **Slow path** on a schedule or manual trigger: integration, scanners, SBOM.
- **Fail closed**: security checks should fail the build unless explicitly waived with rationale.
- **Time-box** jobs (`timeout-minutes`) and add `concurrency` to avoid duplicate work.
- For GitLab, prefer `workflow: rules` and per-job `rules` to avoid duplicate pipelines.

## Branching & release flow (mcr/*)
- Default branch: `mcr/main`.
- Feature work: `mcr/feature/<name>` → merge to `mcr/main`, then merge into `mcr/staging` for tests/builds.
- If `github/*` branches exist locally or on `origin` (fork mode), treat them as read-only mirrors and keep feature implementation on `mcr/feature/*` only.
- In fork mode, sync `origin/github/mcr/main -> github/mcr/main -> mcr/main` before release patch checks.
- In fork mode, run release patch checks on `mcr/main` only, then promote `mcr/main -> mcr/staging -> mcr/release`.
- Release branch: `mcr/release` holds the final shipped state; CI should run on `mcr/staging` and `mcr/release`.
- Release builds are triggered by protected release tags that must point to the tip of `mcr/release` (enforce in CI).

## Workspace integration map (`CODEX_WS_*`)
- Keep shared-workspace topology checks scoped to these roots; this does not limit repo-level CI editing or skill selection.

## GitLab delivery -> GitHub release handoff
- For GitLab-driven GitHub sync, include shared jobs through `GL_CICD_SHARED_PROJ` with `/github/validate.yml` and `/github/push.yml`; shared internals pull `/github/version.yml`, `/patches/patches.yml`, and `/github/visibility.yml`.
- For GitLab release-asset publishing to GitLab Generic Packages, add `/gitlab/validate.yml`, `/gitlab/release.yml`, and a stack build include (for example `/rustc/release-build.yml`).
- Keep release jobs limited to protected refs: `mcr/release` and protected release tags; explicitly block `main` and `mcr/main` in delivery rules.
- Keep variable contracts centralized in `$CODEX_HOME/snippets/ci/gitlab_delivery_vars.env`; avoid ad-hoc per-repo key drift.
- Prefer shared include defaults for delivery variables; set repo-local overrides only where behavior intentionally differs.
- Keep delivery mutation order deterministic: `checkout -> true sync -> version bump -> patch apply -> push` (against the release ref).
- Keep release overlay patches deterministic via `patches/release/series` (fallback sorted `patches/release/*.patch`); shared patch helpers enforce these defaults while still honoring `APPLY_PATCHES*` controls.
- Ensure target repositories include `patches/` and `scripts/` only when delivery automation actually needs them, so release workflows stay predictable without forcing unused layout on unrelated repos.
- Use a repository-defined protected release tag format and push it on the tip commit of `mcr/release`.

## Cross-platform pipeline topology
- GitHub App webhooks can be normalized by an external dispatcher (for example, a Cloudflare Worker), which then dispatches wrapper workflows and GitLab triggers.
- Organization-specific wrapper repos (`gh-actions-upstream`, `gh-actions-xf-checkout`, `gh-actions-xf-main`, `gh-actions-xf-secops`) should stay thin and delegate to shared reusable workflows.
- Shared workflow repos (`gh-actions-shared`) own event/input validation, branch-policy enforcement, shared-ref allowlists, and BWS secret materialization.
- Release helper workflows/actions in `gh-actions` should be pinned by immutable SHA and treated as the publish contract baseline.
- GitLab delivery repos compile/build on protected refs, then push release branches/tags to GitHub release org repos.
- GitHub release workflows (`gh-actions`) validate protected release tags, enforce release-tip checks, and publish artifacts/notes from verified CI outputs.
- In fork mode, GitLab trigger payloads from the worker should keep `github/*` mirrors read-only, sync `origin/github/mcr/main -> github/mcr/main -> mcr/main`, run patch checks on `mcr/main`, then promote `mcr/staging` and `mcr/release`.

## Platform playbooks
- GitHub Actions: `github-actions.md`
- GitLab CI: `gitlab-ci.md`

## Skill routing
- Use skill `ci-github-actions`.
- Use skill `ci-github-actions-fix`.
- Use skill `ci-gitlab-cicd`.
- Use skill `repo-ops`.

## Reproducibility
- Pin toolchains (Rust toolchain file, Python version, Node version).
- Commit lockfiles.
- Avoid network calls in test steps unless required (prefer vendored deps or lockfile + cache).
- Prefer deterministic installers:
  - Rust: `cargo build --locked`
  - Node: `npm ci` / `pnpm install --frozen-lockfile`
  - Python: pinned requirements or a lockfile (`uv.lock`, `poetry.lock`, `requirements.txt` with hashes)

## Supply-chain controls
- Enable dependency review on PRs.
- Require signed commits/tags if policy demands.
- Prefer minimal permissions in GitHub Actions (`contents: read` by default; add write scopes only per job).
- Pin GitHub Actions by major version at minimum; pin to commit SHA for high-assurance environments.

## Secrets managers
- Prefer short-lived credentials and external secrets managers.
- For Bitwarden Secrets Manager, keep CI variables explicit as `BWS_ACCESS_TOKEN` and `BWS_PROJECT_ID`.

## Templates
- GitHub Actions workflows: `$CODEX_HOME/templates/ci/github-actions/`
- GitLab CI workflows: `$CODEX_HOME/templates/ci/gitlab-ci/`
- Minimal permissions snippet: `$CODEX_HOME/snippets/ci/github_actions_min_permissions.yml`
- GitHub release/wrapper vars snippet: `$CODEX_HOME/snippets/ci/github_release_vars.env`
- GitHub release templates: `$CODEX_HOME/templates/ci/github-actions/release-build.yml`, `$CODEX_HOME/templates/ci/github-actions/release-publish.yml`
- GitLab Rust release template: `$CODEX_HOME/templates/ci/gitlab-ci/rust-release-delivery.yml`

## Codex source alignment checklist
- Keep artifact-build/tag-guard behavior aligned with `.github/workflows/build-codex-rs.yml`.
- Keep release publish orchestration aligned with `.github/workflows/release-codex-rs.yml` (including reusable workflow SHA pinning).
- Keep post-publish release hooks aligned with `.github/workflows/publish-codex-rs.yml`.
- Keep GitLab delivery include/rules/variables aligned with `<codex-source-repo>/.gitlab-ci.yml` and `${GL_CICD_SHARED_PROJ}` shared templates.
- Validate helper script expectations against `<codex-source-repo>/scripts/release/bump_version.py`, `<codex-source-repo>/scripts/release/codex_version.py`, and `<codex-source-repo>/scripts/release/check_release_patches.sh`.

## Security checkpoints
- Enforce least-privilege tokens per stage; keep deploy credentials unavailable to untrusted branches.
- Treat scanner and policy bypasses as expiring exceptions with owner and rationale.
- Review artifact/log retention so pipelines do not leak secrets or sensitive build metadata.

## Testing checkpoints
- Define fast-path SLA and ensure every PR runs deterministic lint/unit gates.
- Require flaky-job triage evidence before rerun-only fixes are accepted.
- Verify matrix coverage for supported toolchains/platforms used in release artifacts.

## Deployment checkpoints
- Promote immutable artifacts from verified builds; never rebuild at deploy time.
- Gate production deploy with environment approvals plus automated smoke checks.
- Record rollback artifact ID and command in pipeline output for each release attempt.

## Multi-agent handoff
- Pipeline editor hands trigger/rules diff and expected graph changes to reviewers.
- Security owner signs off permission and secret-scope edits before merge.
- Release operator receives run URL, artifact IDs, and outstanding manual gates.
See also:
- `overview.md`
- `codex-repo.md`
- `../security/supply-chain-controls.md`
- `dependency-updates.md`
- `github-actions.md`
- `gitlab-ci.md`
- `$CODEX_HOME/index/pack/workflows.md`
- `$CODEX_HOME/index/core/ci-cd.md`
