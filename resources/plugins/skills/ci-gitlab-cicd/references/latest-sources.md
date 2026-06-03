---
title: ci-gitlab-cicd reference bundle
status: active
owner: Matthew Cramer
tags:
- skills
- all
- ci-gitlab-cicd
- references
- latest-sources-md
- latest-sources
- user
- web
updated: '2026-02-20'
---
# ci-gitlab-cicd reference bundle

- Last refreshed: 2026-02-11 (UTC)
- Freshness method: web.run lookups against primary vendor/project documentation roots.

## Skill purpose
Build GitLab CI/CD pipelines with security gates, pinned images, and deterministic tooling.

## SKILL.md coverage checklist
- Use this skill when
- Workflow
- GitLab delivery contract
- Agent orchestration
- Validation and testing
- Outputs
- References

## Local implementation anchors
- `../SKILL.md`
- `../agents/openai.yaml`

## External references
- [Git documentation](https://git-scm.com/doc) - Core git behavior and safe workflows.
- [GitHub Actions docs](https://docs.github.com/actions) - Workflow syntax and security hardening.
- [GitLab CI/CD docs](https://docs.gitlab.com/ci/) - Pipeline orchestration and variables.
- [GitLab CI YAML reference](https://docs.gitlab.com/ee/ci/yaml/) - Deterministic pipeline key definitions.

## Proof-of-concept prompts
- Build a minimum viable runbook for `ci-gitlab-cicd` using the checklist above, then validate inputs, timeouts, and rollback notes.
- Produce one positive-path and one negative-path test scenario aligned to `ci-gitlab-cicd` before finalizing changes.

