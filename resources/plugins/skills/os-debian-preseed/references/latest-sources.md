---
title: os-debian-preseed reference bundle
status: active
owner: Matthew Cramer
tags:
- skills
- all
- os-debian-preseed
- references
- latest-sources-md
- latest-sources
- user
- infra
updated: '2026-02-20'
---
# os-debian-preseed reference bundle

- Last refreshed: 2026-02-11 (UTC)
- Freshness method: web.run lookups against primary vendor/project documentation roots.

## Skill purpose
Create Debian preseed files for unattended installations.

## SKILL.md coverage checklist
- Use this skill when
- Workflow
- Agent orchestration
- Validation and testing
- Outputs
- References

## Local implementation anchors
- `../SKILL.md`
- `../agents/openai.yaml`
- `../scripts/skill_helper.py`

## Reference files in this directory
- `latest-sources.md`
- `operations-checklist.md`
- `risk-register.md`

## External references
- [Debian installer preseed guide](https://www.debian.org/releases/stable/amd64/apbs04.en.html) - Preseed directive behavior and examples.

## Proof-of-concept prompts
- Build a minimum viable runbook for `os-debian-preseed` using the checklist above, then validate inputs, timeouts, and rollback notes.
- Produce one positive-path and one negative-path test scenario aligned to `os-debian-preseed` before finalizing changes.
