---
title: DB SQLite3 Rules
status: active
owner: Matthew Cramer
tags:
- skills
- all
- sqlite3
- rules
- rules-md
- user
- default
updated: '2026-03-11'
---
# DB SQLite3 Rules

## Required checks
- Follow the workflow in `../SKILL.md`.
- Prefer deterministic scripts in `../scripts/`.
- Use references in `../references/` for factual guidance.
- Prefer read-only commands first and bound result sizes before inspecting live data.
- Wrap write-oriented SQL in explicit transactions with a documented rollback path.
