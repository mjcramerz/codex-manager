---
title: Mobile Wireless Defense Rules
status: active
owner: Matthew Cramer
tags:
- skills
- all
- mobile-wireless-defense
- rules
- rules-md
- user
- security-labs
updated: '2026-02-20'
---
# Mobile Wireless Defense Rules

## Required checks
- Follow the workflow in `../SKILL.md`.
- Prefer deterministic scripts in `../scripts/`.
- Use references in `../references/` for factual guidance.
- Run `../scripts/mobile_scope_guard.py` before device or wireless assessments.
- Require listed device IDs, allowed operation classes, and an unexpired scope window.
- Refuse network access outside the documented scope, covert payload delivery, or anti-theft bypass requests.
