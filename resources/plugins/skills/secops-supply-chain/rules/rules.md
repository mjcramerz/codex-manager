---
title: Secops Supply Chain Rules
status: active
owner: Matthew Cramer
tags:
- skills
- all
- secops-supply-chain
- rules
- rules-md
- admin
updated: '2026-02-20'
---
# Secops Supply Chain Rules

## Required checks
- Follow the workflow in `../SKILL.md`.
- Prefer deterministic scripts in `../scripts/`.
- Use references in `../references/` for factual guidance.
- Require pinned versions, committed lockfiles, and explicit dependency-change rationale.
- Avoid unsafe install patterns (`curl|sh`, floating tags, unsigned binaries) by default.
- Capture audit/SBOM/provenance evidence (or explicit gap notes) for release-critical changes.
