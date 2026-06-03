# Release workflow

Start with `$CODEX_HOME/plans/workflows/workflow-release.md` before executing this workflow.
Purpose: ship reproducible, auditable releases.


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
- For branch/ref policy and CI gate design, use `ci-cd.md`.
- For GitLab pipeline include/rules details, use `gitlab-ci.md`.
- For repository/tag automation guardrails, use `repo-ops.md`.

## Steps
1) Ensure `mcr/main` is the validated source (including release patch checks on `mcr/main`; in fork mode, after `origin/github/mcr/main -> github/mcr/main -> mcr/main` sync).
2) Promote `mcr/main -> mcr/staging` and verify staging CI/audit gates are green.
3) Promote `mcr/staging -> mcr/release` (fast-forward preferred).
4) Update version (single source of truth).
5) Update changelog (human-focused).
6) Tag release commit with a protected release tag on the tip of `mcr/release` (annotated tag).
7) Build artifacts in CI (reproducible).
8) Generate SBOM.
9) Sign artifacts/tags if required.
10) Publish release notes.


## Supply-chain hardening (recommended)
- Use pinned toolchains and lockfiles; prefer `--locked`/frozen installs.
- Build once, deploy many: reuse the same artifact across environments.
- Record provenance/attestations if your platform supports it (SLSA-style).

## GitLab delivery + GitHub release guardrails
- Tag from the exact tip commit of `mcr/release`; fail closed if tag SHA and `origin/mcr/release` differ.
- In fork mode (`github/*` mirrors present), verify `origin/github/mcr/main -> github/mcr/main -> mcr/main` sync and successful patch checks on `mcr/main` before promoting to `mcr/release`.
- Keep consumer includes minimal (`/github/validate.yml`, `/github/push.yml`) so shared includes (`/github/version.yml`, `/patches/patches.yml`, `/github/visibility.yml`) stay centrally managed in `GL_CICD_SHARED_PROJ`.
- Keep repository release automation in repo-local release helper scripts (for example `scripts/release/get_version.py` and `scripts/release/bump_version.py`) and avoid manual version edits in release commits.
- Keep variable contracts aligned with `$CODEX_HOME/snippets/ci/gitlab_delivery_vars.env`.
- Prefer shared include defaults for delivery variables; set repo-local overrides only when release behavior intentionally differs.
- Keep release overlays in `patches/release/series` (fallback sorted `patches/release/*.patch`) so GitLab delivery patch application stays deterministic.
- Keep release sync mutation order deterministic: `checkout -> true sync -> version bump -> patch apply -> push` (from the `mcr/release` tip).
- When publishing release assets to GitLab Generic Package Registry, keep `/gitlab/validate.yml`, `/gitlab/release.yml`, and stack build include(s) enabled with protected vars: `GL_RELEASE_ASSET`, `GL_GROUP_TOP_RELEASE`, `GL_PAT_RELEASE_TOKEN`, `GL_CICD_RUNNER_BUILD`, `GL_CICD_RUNNER_RELEASE`.

## Codex source release profile
- Validate tag/version rules in `.github/workflows/build-codex-rs.yml` (release-tip check + tag policy validation).
- Validate publish handoff in `.github/workflows/release-codex-rs.yml` (tag resolution from workflow-run SHA + reusable workflow call).
- Keep reusable release callsites pinned to immutable SHAs (current codex-source pin: `4ad5d3f542f960875f7bc3b17fec77e25b62d3f6`).
- Keep `.github/workflows/publish-codex-rs.yml` aligned as the post-publish event hook (or document if intentionally disabled/minimal).
- Keep release artifact expectations aligned with current source outputs (`codex-rs-<target>-<version>.tar.gz` + checksum file).

## Security checkpoints
- Verify signing keys/tokens are valid, scoped, and rotated before tagging or publishing.
- Attach SBOM/provenance artifacts to the release and confirm integrity checks pass.
- Block release if `mcr/release` plus release-tag policy or approval requirements are violated.

## Testing checkpoints
- Require green staging gates plus release-smoke checks on the exact signed artifact.
- Re-run critical integration/security checks after final tag creation when workflows require it.
- Capture run IDs, checksums, and approvals in the release checklist or notes.

## Deployment checkpoints
- Promote in order: `mcr/staging` validation -> `mcr/release` tag -> publish channels.
- Keep previous signed artifact and tag ready for immediate rollback.
- Assign post-release monitoring owner and rollback thresholds before publish.

## Multi-agent handoff
- Release coordinator assigns ownership for tagging, artifact verification, and notes publication.
- CI owner hands run URLs, artifact digests, and signing results to the publisher.
- Operations owner confirms rollout completion and rollback readiness before closure.
See also:
- `overview.md`
- `codex-repo.md`
- `ci-cd.md`
- `../security/supply-chain-controls.md`
- Use skill `repo-ops`.
- Use skill `secops-supply-chain`.
- `$CODEX_HOME/index/pack/workflows.md`
