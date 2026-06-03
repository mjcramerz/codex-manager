# Workflow plans (overview)
Canonical catalog of workflow plan templates.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Use when
- executing a workflow that requires a structured plan
- you want the plan that matches a workflow playbook
- you need consistent checkpoints across workflow runs

- Apply universal planning gates from `$CODEX_HOME/plans/OVERVIEW.md` (PoC, integration/API, implementation, and operational readiness).

## Contents
<!-- BEGIN:contents -->
- `$CODEX_HOME/plans/workflows/workflow-agent-orchestration.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-aide.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-ansible.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-auditd.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-browsers.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-build-an-app.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-bws-local.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-ci-cd.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-code-review.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-codex-repo.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-containers.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-crowdsec.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-debian-preseed.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-dependency-updates.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-desktop-entries.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-desktop-wayland.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-elastic-stack.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-execpolicy.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-filesystems.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-github-actions.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-gitlab-ci.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-grub.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-kernel-build.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-kubernetes.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-logrotate.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-optimizations.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-overview.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-planning.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-prompts-library.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-proxmox.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-release.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-repo-ops.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-nethunter-pixel9a.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-offsec-defense.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-sysctl.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-systemd.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-terraform.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-testing.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-usbguard.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-virsh.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-vscode-extensions.md` — Plan
- `$CODEX_HOME/plans/workflows/workflow-web-frontend.md` — Plan
<!-- END:contents -->

## Notes
- File names map to `$CODEX_HOME/docs/workflows/*.md` as `workflow-<name>.md`.
- If a workflow exists without a plan, add one and list it here.

## Security checkpoints
- Confirm trust boundaries, credentials, and least-privilege assumptions before execution.
- Validate input bounds, timeout/retry limits, and failure behavior for risky operations.
- Record any approved exception, owner, and expiry before proceeding.

## Testing checkpoints
- Define fast-path and deep validation commands before making changes.
- Capture expected outcomes and acceptance criteria for each validation step.
- Re-run impacted checks after major changes and before final handoff.

## Deployment checkpoints
- Document rollout order, blast-radius controls, and rollback conditions.
- Confirm migration/backfill or feature-flag sequencing when applicable.
- Record post-deploy verification owners and evidence.

## Multi-agent handoff
- Coordinator hands off scope, constraints, and stop condition with the target entrypoint.
- Executor reports touched files, commands run, evidence, blockers, and next action.
- Receiving agent acknowledges handoff completeness before continuing execution.

## Related
- `../OVERVIEW.md`
- `$CODEX_HOME/index/pack/workflows.md`
- `$CODEX_HOME/index/pack/plans.md`

## Examples

- Example objective: "<short task statement>"
- Example validation: "<command or check>"
