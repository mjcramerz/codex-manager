---
title: OffSec Defense Rules
status: active
owner: Matthew Cramer
tags:
- skills
- all
- offsec-defense
- rules
- rules-md
- user
- security-labs
updated: '2026-02-20'
---
# OffSec Defense Rules

## Required checks
- Follow the workflow in `../SKILL.md`.
- Prefer deterministic scripts in `../scripts/`.
- Use references in `../references/` for factual guidance.
- Run `../scripts/scope_guard.py` before dual-use operations and fail closed on scope errors.
- Require `scope_id`, `lab_only=true`, and an unexpired `expires_utc` window.
- Refuse requests outside documented ownership/scope or requests that enable stealth abuse.
