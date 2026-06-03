# Workflow catalog
Purpose: map recurring task types to operational playbooks and help the agent choose one workflow before editing.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Use this file when
- you need to choose the right operational playbook
- you are mapping a workflow to a plan template
- you are maintaining workflow routing or execution guidance

## Workflow catalog
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

## Selection guide
- Process and coordination -> `planning.md`, `agent-orchestration.md`, `repo-ops.md`
- Validation and review -> `testing.md`, `code-review.md`, `dependency-updates.md`
- Build and delivery -> `ci-cd.md`, `github-actions.md`, `gitlab-ci.md`, `release.md`
- System and infra -> `filesystems.md`, `systemd.md`, `grub.md`, `kernel-build.md`, `containers.md`, `kubernetes.md`, `terraform.md`, `proxmox.md`, `virsh.md`
- Security and defensive ops -> `bws-local.md`, `auditd.md`, `crowdsec.md`, `aide.md`, `usbguard.md`, `offsec-defense.md`, `nethunter-pixel9a.md`
- UX and frontend -> `web-frontend.md`, `build-an-app.md`, `prompts-library.md`, `desktop-wayland.md`, `desktop-entries.md`, `browsers.md`

## Maintenance rules
- Every workflow added here should have a corresponding plan under `$CODEX_HOME/plans/workflows/` when the execution path is non-trivial.
- Prefer tool-agnostic workflow guidance unless a specific runtime primitive is guaranteed by contract.
- Do not reference missing runtime directories as required prerequisites.

## Related
- `$CODEX_HOME/index/pack/workflows.md`
- `$CODEX_HOME/plans/OVERVIEW.md`
- `$CODEX_HOME/plans/workflows/overview.md`
