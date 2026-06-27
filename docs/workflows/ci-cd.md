# CI/CD workflow

Start with `$CODEX_HOME/plans/workflows/workflow-ci-cd.md` before executing this workflow.
Purpose: provide canonical CI/CD guidance for this pack.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/workflows/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Direct routing
- If you are defining cross-platform CI policy, start here.
- If you are editing GitHub workflows/wrappers, route to `github-actions.md`.
- If you are editing `.gitlab-ci.yml` or shared delivery includes, route to `gitlab-ci.md`.
- If you are editing Cloudflare Worker plus delivery-template repos, route to `cloudflare-delivery.md`.
- If you are preparing release tagging/publish steps, route to `release.md`.

## Adjacent repo map
- `delivery` owns the shared GitLab CI/CD include graph.
- `cf-git-cicd-worker` and `cf-aptly-r2` are current repo-grounded examples of Worker plus shared-delivery contracts.
- `codex-manager` owns the runtime-pack and plugin-skill guidance that should mirror CI/release behavior.

## CI gates (recommended)
1) Format
2) Lint/static analysis
3) Unit tests
4) Integration tests (as appropriate)
5) Dependency vulnerability audit
6) Secret scanning (baseline)
7) SBOM generation (release builds)
8) Artifact signing (org policy)

## Delivery rules
- Keep release jobs limited to protected refs and protected release tags.
- Keep variable contracts centralized in `$CODEX_HOME/snippets/ci/gitlab_delivery_vars.env`.
- Keep delivery mutation order deterministic: `checkout -> true sync -> version bump -> patch apply -> push`.
- Keep shared delivery logic centralized when multiple repos consume the same contract.

## Security checkpoints
- Enforce least-privilege tokens per stage; keep deploy credentials unavailable to untrusted branches.
- Treat scanner and policy bypasses as expiring exceptions with owner and rationale.
- Review artifact/log retention so pipelines do not leak secrets or sensitive build metadata.

## See also
- `gitlab-ci.md`
- `github-actions.md`
- `cloudflare-delivery.md`
- `release.md`
