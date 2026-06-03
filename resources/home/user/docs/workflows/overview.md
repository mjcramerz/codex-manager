# Workflows overview

Maintenance contract:
- Create/update workflow docs in `$CODEX_HOME/docs/workflows/`.
- Treat `$CODEX_HOME/docs/workflows/` as runtime materialized content.


## Contents
<!-- BEGIN:contents -->
- `$CODEX_HOME/docs/workflows/agent-orchestration.md` — Agent orchestration workflow
- `$CODEX_HOME/docs/workflows/aide.md` — AIDE workflow
- `$CODEX_HOME/docs/workflows/ansible.md` — Ansible workflow
- `$CODEX_HOME/docs/workflows/auditd.md` — auditd workflow
- `$CODEX_HOME/docs/workflows/browsers.md` — Browsers workflow
- `$CODEX_HOME/docs/workflows/build-an-app.md` — Workflow: build an app (end-to-end)
- `$CODEX_HOME/docs/workflows/bws-local.md` — Local BWS workflow
- `$CODEX_HOME/docs/workflows/ci-cd.md` — CI/CD workflow
- `$CODEX_HOME/docs/workflows/code-review.md` — Code review workflow
- `$CODEX_HOME/docs/workflows/codex-repo.md` — Codex repository workflow
- `$CODEX_HOME/docs/workflows/containers.md` — Containers workflow
- `$CODEX_HOME/docs/workflows/crowdsec.md` — CrowdSec workflow
- `$CODEX_HOME/docs/workflows/debian-preseed.md` — Debian preseed (unattended installation)
- `$CODEX_HOME/docs/workflows/dependency-updates.md` — Dependency update workflow
- `$CODEX_HOME/docs/workflows/desktop-entries.md` — Desktop entries workflow
- `$CODEX_HOME/docs/workflows/desktop-wayland.md` — Wayland desktop workflow
- `$CODEX_HOME/docs/workflows/elastic-stack.md` — Elastic Stack workflow
- `$CODEX_HOME/docs/workflows/execpolicy.md` — Execpolicy workflow
- `$CODEX_HOME/docs/workflows/filesystems.md` — Filesystems workflow
- `$CODEX_HOME/docs/workflows/github-actions.md` — GitHub Actions workflow
- `$CODEX_HOME/docs/workflows/gitlab-ci.md` — GitLab CI/CD workflow
- `$CODEX_HOME/docs/workflows/grub.md` — GRUB workflow
- `$CODEX_HOME/docs/workflows/kernel-build.md` — Kernel build workflow
- `$CODEX_HOME/docs/workflows/kubernetes.md` — Kubernetes workflow
- `$CODEX_HOME/docs/workflows/logrotate.md` — logrotate workflow
- `$CODEX_HOME/docs/workflows/optimizations.md` — Host optimizations workflow
- `$CODEX_HOME/docs/workflows/planning.md` — Planning workflow
- `$CODEX_HOME/docs/workflows/prompts-library.md` — Prompts library workflow
- `$CODEX_HOME/docs/workflows/proxmox.md` — Proxmox workflow
- `$CODEX_HOME/docs/workflows/release.md` — Release workflow
- `$CODEX_HOME/docs/workflows/repo-ops.md` — Repo operations workflow
- `$CODEX_HOME/docs/workflows/nethunter-pixel9a.md` — NetHunter Pixel 9a workflow
- `$CODEX_HOME/docs/workflows/offsec-defense.md` — OffSec defense workflow
- `$CODEX_HOME/docs/workflows/sysctl.md` — sysctl workflow
- `$CODEX_HOME/docs/workflows/systemd.md` — systemd workflow
- `$CODEX_HOME/docs/workflows/terraform.md` — Terraform workflow
- `$CODEX_HOME/docs/workflows/testing.md` — Testing workflow
- `$CODEX_HOME/docs/workflows/usbguard.md` — USBGuard workflow
- `$CODEX_HOME/docs/workflows/virsh.md` — virsh / KVM workflow
- `$CODEX_HOME/docs/workflows/vscode-extensions.md` — VS Code extensions
- `$CODEX_HOME/docs/workflows/web-frontend.md` — Web frontend workflow
<!-- END:contents -->


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Plan
Use workflows to identify the right plan template, then plan **before coding** when any trigger applies (see `planning.md`).
Workflow-specific plan catalog: `$CODEX_HOME/plans/workflows/overview.md`.

## Required routing contract
- `$CODEX_HOME/AGENTS.md`
- `$CODEX_HOME/memories/MEMORY.md` (use `default` when unsure)
- `$CODEX_HOME/INDEX.md`
- `$CODEX_HOME/index/pack/plans.md` + `$CODEX_HOME/index/pack/workflows.md`
- `$CODEX_HOME/index/pack/skills.md`
- follow `$CODEX_HOME/UNIX.md` before command execution

## Direct routing
- If you are updating CI or release policy across platforms, start with `ci-cd.md`.
- If you are editing GitHub workflow files or wrappers, use `github-actions.md`.
- If you are editing `.gitlab-ci.yml` delivery includes/rules, use `gitlab-ci.md`.
- If you are running tagging/publish steps, use `release.md`.
- If you are changing branch, tag, or automation scripting hygiene, use `repo-ops.md`.
- If you are retiring legacy memory-runtime references or updating runtime-home sync guidance, use `codex-repo.md` or `repo-ops.md`.
- If you are configuring local Bitwarden Secrets Manager usage on Debian, use `bws-local.md`.
- If the task is tied to a repository rollout, check `$CODEX_HOME/rollouts/OVERVIEW.md` and the repository rollout plan first.

## Core workflows
- Agent orchestration: `agent-orchestration.md`
- Role matrix and spawn guide: `$CODEX_HOME/MULTI_AGENT.md`
- Codex repository alignment: `codex-repo.md`
- Testing: `testing.md`
- Execpolicy: `execpolicy.md`

## CI platforms
- CI/CD cross-platform strategy: `ci-cd.md`
- GitHub pipelines and wrappers: `github-actions.md`
- GitLab pipelines and delivery: `gitlab-ci.md`
- Release execution: `release.md`
- Repo automation guardrails: `repo-ops.md`

## Security & hardening
- Local BWS lifecycle: `bws-local.md` + `../security/bitwarden-secrets-local.md`
- NetHunter Pixel 9a: `nethunter-pixel9a.md` + `../security/nethunter-pixel9a.md`
- OffSec defense: `offsec-defense.md` + `../security/offsec-defense.md`
- Security operations knowledge base: `../security/security-labs-index.md`

## Platform workflows
- Web frontend: `web-frontend.md`

## Build & scaffolding
- End-to-end build flow: `build-an-app.md`
- Dependency hygiene: `dependency-updates.md`
- Prompt maintenance: `prompts-library.md`

## Infrastructure & ops
- Containers: `containers.md`
- Kubernetes: `kubernetes.md`
- Systemd/logrotate/filesystems: `systemd.md`, `logrotate.md`, `filesystems.md`
- Virtualization: `proxmox.md`, `virsh.md`

## Observability
- Elastic stack: `elastic-stack.md`
- Audit and abuse defenses: `auditd.md`, `crowdsec.md`, `aide.md`

## System hardening
- Kernel and boot: `kernel-build.md`, `grub.md`
- Runtime controls: `sysctl.md`, `usbguard.md`, `optimizations.md`

## Desktop
- Browser and desktop stacks: `browsers.md`, `desktop-wayland.md`, `desktop-entries.md`

## Skill shortcuts
- Use skill `workflow-plans`.
- Use skill `ci-github-actions`.
- Use skill `ci-gitlab-cicd`.
- Use skill `repo-ops`.
- Use skill `quality-code-review`.

## Security checkpoints
- Confirm the selected workflow covers the active trust boundary (code, CI, release, or repo policy).
- Carry forward secret/auth assumptions from the chosen workflow instead of ad-hoc exceptions.
- If multiple workflows apply, adopt the strictest posture and document why.

## Testing checkpoints
- Capture the minimum command set from the selected workflow before editing (fast path plus deep path).
- Preserve prior evidence (command output, artifacts, risk notes) when hopping between workflows.
- Revalidate workflow links when this overview or referenced workflows are updated.

## Deployment checkpoints
- Verify the chosen workflow names rollout order, rollback trigger, and post-deploy owner.
- Check branch/tag policy alignment when moving between CI/CD, release, and repo-ops workflows.
- Treat workflow doc changes as deployable assets and run pack verification before handoff.

## Multi-agent handoff
- Share the exact workflow file and plan template each agent must follow.
- Require every agent to follow AGENTS -> MEMORY -> INDEX -> plans/workflows -> skills -> `$CODEX_HOME/UNIX.md` before execution.
- Require agents to report workflow deviations, not only file diffs.
- Close with a reconciled checklist showing completed checkpoints across involved workflows.

## References
- `$CODEX_HOME/templates/OVERVIEW.md`
- `$CODEX_HOME/index/pack/workflows.md`
- `$CODEX_HOME/plans/OVERVIEW.md`
