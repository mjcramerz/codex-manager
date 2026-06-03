# $CODEX_HOME/templates/ (OVERVIEW)
Purpose: provide project skeletons and repo hygiene files you can copy into a new (or existing) repo.

Maintenance contract:
- Create/update templates in `$CODEX_HOME/templates/`.
- Treat `$CODEX_HOME/templates/` as runtime materialized content.

## Multi-agent handoffs
- Share this entrypoint plus the AGENTS → INDEX → entrypoint order with any agent you `spawn_agent`.
- Log the handoff (entrypoint + stop condition) and keep status visible via `send_input`/`wait`/`close_agent` so reviewers can trace who handled which area.

## Inputs
- Template source path under `$CODEX_HOME/templates/`.
- Destination repository path.
- Pinned runtime/image/action versions and repo policy constraints.

## Outputs
- Copied template files with deterministic paths.
- Template-specific Inputs/Outputs/Next steps from each `overview.md`.
- Optional repo hygiene files from `common/`.

## Next steps
1) Copy a template directory into your repo (for example `cp -a`) and follow its `overview.md`.
2) Replace placeholders (`CHANGE_ME`, sample versions, org names) with pinned repo values before first commit.
3) Use `$CODEX_HOME/docs/templates/using-templates.md` for the full checklist.

## Template contract (required)
- Each template `overview.md` must declare **Inputs** (variables, versions, paths).
- List **Outputs** (files created/modified) and **Next steps**.
- Include exact commands to build/test/run when applicable.
- CI template overviews must include branch/tag guardrails and shared include contracts when applicable.

## Common (repo hygiene)
- `common/`: `common/CODEOWNERS`, `common/CONTRIBUTING.md`, `common/SECURITY.md` (add `common/.editorconfig`/`common/.gitattributes` if your org requires them)
- `common/.github/`: shared `.github/` defaults (`dependabot.yml`, `pull_request_template.md`)
- `common/repo-delivery-layout/`: root `patches/` + `scripts/` layout with `get_version.py`/`bump_version.py`
- `common/posix-sh-script/`: POSIX/BusyBox shell script skeleton

## Prompts
- `$CODEX_HOME/templates/prompts/slash-command-maintenance/`: slash-command prompt maintenance scaffold

## Bash / sh
- Read `$CODEX_HOME/UNIX.md` before choosing a shell-specific template.
- `bash/script-skeleton/`: Bash script skeleton
- `sh/posix-sh-script/`: POSIX sh script skeleton

## CI (GitHub Actions)
- `ci/github-actions/`: ready-to-copy workflows (node/python/rust/security + release build/publish scaffolds for protected release tags)
## CI (GitLab)
- `ci/gitlab-ci/`: ready-to-copy pipelines (node/python/rust/security + `github-delivery.yml` + `rust-release-delivery.yml` scaffolds using `/github/validate.yml` + `/github/push.yml`; shared internals `/github/version.yml`, `/patches/patches.yml`, `/github/visibility.yml`)

## Infrastructure
- `infra/terraform-module-skeleton/`: Terraform module skeleton
- `infra/ansible-role-skeleton/`: Ansible role skeleton
- `infra/kubernetes-app-skeleton/`: Kubernetes manifest skeleton

## Containers
- `containers/docker-compose-skeleton/`: compose scaffold with online/offline templates + Podman keep-id override
- `containers/dockerfile-skeleton/`: rootless-friendly Dockerfile + `.dockerignore` scaffold
- `containers/devlab-codelab-skeleton/`: dev container scaffold with common tooling (Docker + Podman)

## systemd
- `systemd/service-skeleton/`: service and timer unit skeletons
- `systemd/user-service-skeleton/`: user-level service skeletons

## Filesystems
- `filesystems/ops-scripts/`: safe plan/apply helpers for mkfs/fstab

## Virtualization
- `virtualization/vagrant-libvirt-skeleton/`: Vagrantfile scaffold for libvirt
- `virtualization/debian-preseed/`: Debian unattended install baseline
- `virtualization/proxmox-vm-skeleton/`: Proxmox VM notes + cloud-init
- `virtualization/virsh-vm-skeleton/`: libvirt domain skeleton

## Python
- `python/fastapi-app/`: FastAPI API scaffold
- `python/cli-app/`: Python CLI scaffold

## Rust
- `rust/axum-api/`: Axum API scaffold
- `rust/cli-app/`: Rust CLI scaffold

## Go
- `go/cli-app/`: Go CLI scaffold

## TypeScript
- `typescript/ts-lib/`: TypeScript library skeleton

## Web
- `web/react-vite-app/`: React + Vite + TypeScript scaffold
- `web/nextjs-app/`: Next.js scaffold wrapper
- `web/sveltekit-app/`: SvelteKit scaffold wrapper
- `web/vue-app/`: Vue scaffold wrapper
- `web/nuxt-app/`: Nuxt scaffold wrapper
- `web/htmx-app/`: HTMX skeleton
- `web/html-static/`: static HTML skeleton

## Observability
- `observability/elastic-stack-compose/`: Elastic Stack compose skeleton
- `observability/auditd-rules-skeleton/`: auditd rules baseline
- `observability/logrotate-skeleton/`: logrotate baseline
- `observability/aide-skeleton/`: AIDE baseline
- `observability/crowdsec-skeleton/`: CrowdSec baseline

## System hardening
- `system/kernel-build-skeleton/`: kernel build notes + config fragment
- `system/grub-baseline/`: GRUB defaults
- `system/sysctl-baseline/`: sysctl baseline
- `system/offsec-defense-kit/`: scoped offsec-defense starter kit
- `system/mobile-wireless-defense-kit/`: scoped mobile and wireless defense starter kit
- `system/nethunter-pixel9a-kit/`: scoped Pixel 9a NetHunter kernel-porting and root-lab starter kit
- `system/usbguard-baseline/`: USBGuard rules baseline

## Desktop
- `desktop/wayland-skeleton/`: Labwc/Wayland configs
- `desktop/desktop-entry/`: `.desktop` launcher template

## Related
- Docs: `$CODEX_HOME/docs/`
- Templates overview: `$CODEX_HOME/docs/templates/overview.md`
- Usage guide: `$CODEX_HOME/docs/templates/using-templates.md`
- Templates plan: `$CODEX_HOME/plans/templates-library.md`
- Prompts plan: `$CODEX_HOME/plans/prompts-library.md`
- Snippets: `$CODEX_HOME/snippets/`
- Entry point: `$CODEX_HOME/index/pack/templates.md`
