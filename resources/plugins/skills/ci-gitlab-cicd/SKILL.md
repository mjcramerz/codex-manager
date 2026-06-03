---
name: ci-gitlab-cicd
description: Build and troubleshoot GitLab CI/CD pipelines with deterministic jobs, pinned
  images, reusable templates, and security gates. Use when the user asks to create or fix
  .gitlab-ci.yml pipelines.
metadata:
  version: '1.1'
  short-description: Build deterministic GitLab pipelines with secure delivery defaults
  tags:
  - gitlab
  - ci
  - cd
  - security
  - testing
interface:
  display-name: CI-GitLab CI/CD
  short-description: Build deterministic GitLab pipelines with secure delivery defaults
  icon-small: assets/icon-32.png
  icon-large: assets/icon-128.png
  brand-color: '#4432CC'
  default-prompt: Act as the "CI-GitLab CI/CD" specialist for "Build deterministic GitLab
    pipelines with secure delivery defaults". Deliver focused, deterministic results with
    minimal, reviewable changes and explicit assumptions. Validate untrusted inputs and bounded
    I/O, run the narrowest relevant checks, and report concrete actions, evidence, and residual
    risks.
---

## Use this skill when
- creating or hardening `.gitlab-ci.yml` pipelines
- wiring GitLab->GitHub delivery and optional GitLab package release jobs
- fixing rules/includes/variable drift in shared delivery pipelines

## Inputs
- target `.gitlab-ci.yml` and included templates
- protected ref policy (`mcr/staging`, `mcr/release`, protected release tags)
- delivery intent (GitHub sync only or sync + GitLab package publishing)
- shared include defaults, plus any repo-local variable overrides and secrets source

## Scope and boundaries
- Keep consumer includes minimal: `/github/validate.yml` + `/github/push.yml`.
- For any GitLab-project `.gitlab-ci.yml` create/update request, treat both includes as mandatory.
- Let shared internals own `/github/version.yml`, `/patches/patches.yml`, `/github/visibility.yml`.
- Shared patch helpers currently enforce `patches/release` + `patches/release/series`; keep `PATCH_RELEASE_DIR` and `PATCH_SERIES_FILE` declared for contract visibility.
- Keep mirror branches read-only in fork mode and do feature work from `mcr/feature/*`.
- In fork mode, verify `origin/github/mcr/main -> github/mcr/main -> mcr/main` sync before patch checks.
- In fork mode, run release patch checks on `mcr/main` only before promoting `mcr/main -> mcr/staging -> mcr/release`.

## Workflow
1) Define stage graph and protected-ref rules first.
2) Apply deterministic include + variable contract; avoid per-repo drift.
3) Keep mutation order fixed: `checkout -> true sync -> version bump -> patch apply -> push`.
4) Keep patch order authoritative in `patches/release/series`.
5) If package publishing is enabled, validate `/gitlab/validate.yml`, `/gitlab/release.yml`, and stack release-build include alignment (for example `/rustc/release-build.yml`).
6) Keep paired `.github/workflows/release-*.yml` callsites pinned to the shared `release-from-workflow-run.yml` SHA (which runs shared security gates) and avoid duplicating release-scope security jobs per repo.
7) Validate minimal impacted stages and report residual risk.

## Delivery contract
- Inherit sync vars from shared includes by default and declare only necessary repo-local overrides.
- Keep optional package-release contract explicit when enabled (`GL_RELEASE_ASSET`, release project/token/runner vars).
- Keep `github/*` mirrors read-only in fork mode and enforce protected-ref policy.

## Agent orchestration
- Delegate read-only graph inspection and include/variable audits.
- Reconcile before editing shared blocks or release jobs.

## Validation and testing
- Lint `.gitlab-ci.yml` and verify include resolution before runtime checks.
- Run narrow stage smoke tests for only the changed jobs.
- Verify protected-ref behavior, mirror-branch safety, and release-tag gating.
- Confirm logs/artifacts do not leak secret values or token material.

## Outputs
- Reviewable `.gitlab-ci.yml` diffs with clear delivery rationale.
- Contract checklist (includes, vars, mutation order, patch source).
- Verification evidence.

## References
- `$CODEX_HOME/docs/workflows/gitlab-ci.md`
- `$CODEX_HOME/docs/workflows/release.md`
- `$CODEX_HOME/templates/ci/gitlab-ci/`
- `$CODEX_HOME/templates/ci/gitlab-ci/rust-release-delivery.yml`
- `$CODEX_HOME/snippets/ci/gitlab_delivery_vars.env`
- `$CODEX_HOME/prompts/gitlab_ci_add.md`
