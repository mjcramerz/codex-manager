---
title: C2 Defense Ops Rules
status: active
owner: Matthew Cramer
tags:
- skills
- all
- c2-defense-ops
- rules
- rules-md
- user
- security-labs
updated: '2026-02-20'
---
# C2 Defense Ops Rules

## Required checks
- Follow the workflow in `../SKILL.md`.
- Prefer deterministic scripts in `../scripts/`.
- Use references in `../references/` for factual guidance.
- Run `../scripts/c2_scope_guard.py` before replay/validation activity.
- Require allowed target labels, operation class allowlists, and an unexpired scope window.
- Refuse persistence enablement, credential theft, or stealth abuse requests.
