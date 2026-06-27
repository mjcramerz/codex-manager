# Release workflow

Start with `$CODEX_HOME/plans/workflows/workflow-release.md` before executing this workflow.
Purpose: ship reproducible, auditable releases.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/workflows/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Direct routing
- For branch/ref policy and CI gate design, use `ci-cd.md`.
- For GitLab pipeline include/rules details, use `gitlab-ci.md`.
- For Cloudflare Worker plus shared delivery repos, use `cloudflare-delivery.md`.
- For repository/tag automation guardrails, use `repo-ops.md`.

## Steps
1) Ensure `mcr/main` is the validated source.
2) Promote `mcr/main -> mcr/staging` and verify staging CI/audit gates are green.
3) Promote `mcr/staging -> mcr/release`.
4) Update version and changelog.
5) Tag the release commit on the tip of `mcr/release`.
6) Build artifacts in CI.
7) Generate SBOM and signing artifacts where required.
8) Publish release notes and packages.

## Shared delivery guardrails
- Keep shared GitLab delivery logic in the central `delivery` repository unless intentionally diverging.
- For repos like `cf-git-cicd-worker` and `cf-aptly-r2`, align release notes, routes, and variable contracts with the shared delivery templates they actually consume.
- Keep release overlays deterministic and document the exact publish order in repo-local release docs.

## Security checkpoints
- Verify signing keys/tokens are valid, scoped, and rotated before tagging or publishing.
- Attach SBOM/provenance artifacts to the release and confirm integrity checks pass.
- Block release if protected-ref, protected-tag, or approval requirements are violated.

## See also
- `ci-cd.md`
- `gitlab-ci.md`
- `cloudflare-delivery.md`
- `repo-ops.md`
