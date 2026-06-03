---
title: GITHUB-PR Comments Rules
status: active
owner: Matthew Cramer
tags:
- skills
- all
- github-pr-comments
- rules
- rules-md
- admin
updated: '2026-02-20'
---
# GITHUB-PR Comments Rules

## Required checks
- Follow the workflow in `../SKILL.md`.
- Prefer deterministic scripts in `../scripts/`.
- Use references in `../references/` for factual guidance.
- Run `../scripts/fetch_comments.py` with bounded paging/timeouts before proposing fixes.
- Require user confirmation before posting review responses or mutating PR state.
- Keep comment triage findings mapped to exact file/line references when available.
