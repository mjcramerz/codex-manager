---
name: os-debian-preseed
description: Create Debian preseed automation files for unattended installations with deterministic
  installer behavior. Use when the user asks for Debian auto-install or image provisioning
  via preseed.
metadata:
  version: '1.0'
  short-description: Create Debian preseed files for unattended installations
  tags:
  - debian
  - preseed
  - unattended
  - install
  - virtualization
interface:
  display-name: OS-Debian Preseed
  short-description: Create Debian preseed files for unattended installations
  icon-small: assets/icon-32.png
  icon-large: assets/icon-128.png
  brand-color: '#3265CC'
  default-prompt: Act as the "OS-Debian Preseed" specialist for "Create Debian preseed files
    for unattended installations". Deliver focused, deterministic results with minimal, reviewable
    changes and explicit assumptions. Validate untrusted inputs and bounded I/O, run the narrowest
    relevant checks, and report concrete actions, evidence, and residual risks.
---

## Use this skill when
- generating or updating Debian preseed files
- automating unattended Debian installs
- preparing reproducible VM or bare-metal installs
- grounding changes against the active `debian-preseed-di` repository contract

## Workflow
1) Collect requirements (disk layout, network, users, packages)
2) Choose partitioning strategy and confirm destructive flags
3) Generate password hashes and inject safely
4) Create preseed and host it securely
5) Validate in a VM and verify post-install state

## Agent orchestration
- Confirm that the request fits this skill and state boundaries if other skills are needed.
- For multi-step work, keep a concise plan, execute in small reversible steps, and surface assumptions early.
- Delegate only independent discovery tasks, then reconcile findings before making edits.

## Validation and testing
- Validate critical inputs and bound external I/O (size, retries, and timeouts) before applying changes.
- Run the narrowest relevant checks that prove behavior (tests, lint, or build as applicable).
- Include risk-based negative or edge-case coverage for security-sensitive, parsing, or automation changes.
- Report verification commands, outcomes, and any follow-up checks that remain.

## Outputs
- A preseed file with safe defaults
- Clear installation instructions and validation steps

## Local resources
- `os-debian-preseed/references/latest-sources.md`
- `os-debian-preseed/references/operations-checklist.md`
- `os-debian-preseed/references/risk-register.md`
- `os-debian-preseed/assets/rollback-checklist.md`
- `os-debian-preseed/scripts/skill_helper.py`
- repo anchor: `/data/workspace/gitlab/computes/active/debian-preseed-di/README.md`

## References
- `$CODEX_HOME/index/domains/system/debian-preseed.md`
- `$CODEX_HOME/docs/workflows/debian-preseed.md`
- `$CODEX_HOME/docs/virtualization/debian-preseed.md`
- `$CODEX_HOME/templates/virtualization/debian-preseed/`
- `$CODEX_HOME/snippets/virtualization/preseed_boot_params.txt`
