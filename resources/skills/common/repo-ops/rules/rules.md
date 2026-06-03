---
title: Repo Ops Rules
status: active
owner: Matthew Cramer
tags:
- skills
- all
- repo-ops
- rules
- rules-md
- common
updated: '2026-03-06'
---
# Repo Ops Rules

## Required checks
- Follow the workflow in `../SKILL.md`.
- Prefer deterministic helpers in `../scripts/`.
- Enforce repo-root, branch, remote, and worktree preconditions before mutating refs.
- Require explicit dry-run or equivalent inspection path before risky repo operations.
- Preserve protected branch, promotion-order, and release-tag controls.
- Report rollback notes and touched refs in the final handoff.
