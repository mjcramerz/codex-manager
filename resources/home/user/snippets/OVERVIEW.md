# snippets/ (OVERVIEW)
Purpose: provide copy-ready hardened patterns.
Treat these as starting points and adapt them to repo conventions.

Maintenance contract:
- Create/update snippets in `$CODEX_HOME/snippets/`.
- Use `$CODEX_HOME/snippets/` as runtime-only materialized content.

## Multi-agent handoffs
- Share this entrypoint and AGENTS → INDEX → entrypoint order with any `spawn_agent` worker.
- Record handoff scope/stop condition; track progress with `send_input`, `wait`, and `close_agent`.

## How to use
- Prefer snippets when the repo lacks established patterns.
- Keep behavior consistent with existing code; avoid unnecessary refactors.
- For pack snippet maintenance, start with `$CODEX_HOME/plans/snippets-library.md`.
- For prompt contract snippets, use `$CODEX_HOME/plans/prompts-library.md`.

## Bash
- Detect the active shell via `$CODEX_HOME/AGENTS.md`, then use `$CODEX_HOME/UNIX.md` before copying Bash snippets.
- `bash/strict.sh`: strict mode baseline
- `bash/logging.sh`: structured logging helpers
- `bash/argparse.sh`: argument parsing skeleton
- `bash/script_skeleton.sh`: safe script template
- `bash/repo_ops_helpers.sh`: git/repo safety helpers
- `bash/security_assessment_guardrails.sh`: scope helpers for documented security operations
- `bash/scoped_nmap_inventory.sh`: scope-validated inventory scan helper
- `bash/incident_wireshark_capture.sh`: time-bounded tshark capture helper
- `bash/nethunter_build.sh`: deterministic NetHunter build-tooling helper
- `bash/nethunter_pixel9a_preflight.sh`: Pixel 9a NetHunter preflight evidence collector
- `bash/nethunter_pixel9a_root_sequence.sh`: Pixel 9a root/flash helper with preview mode
- `bash/fs_probe.sh`: read-only filesystem probe
- `bash/fstab_update.sh`: safe UUID-based fstab append


## POSIX sh
- `sh/strict.sh`: strict mode baseline
- `sh/script_skeleton.sh`: safe script template for POSIX/BusyBox

## Python
- `python/logging.py`: structured logging (json/text)
- `python/settings.py`: `pydantic-settings` baseline
- `python/http_client.py`: safe HTTP client defaults (timeouts/retries)
- `python/fastapi_security_headers.py`: conservative security headers middleware
- `python/get_version.py`: deterministic version reader (`auto`, json/toml/yaml/plain/regex)
- `python/bump_version.py`: deterministic app/release version bump helper (`--version <value>`)

## Go
- `go/main.go`: minimal entrypoint

## TypeScript
- `typescript/tsconfig.json`: strict tsconfig baseline

## Rust
- `rust/error.rs`: typed error pattern
- `rust/tracing.rs`: tracing init baseline
- `rust/cli.rs`: CLI parsing baseline
- `rust/axum_timeout_layer.rs`: timeouts/layers example

## systemd
- `systemd/service.unit`: hardened service unit skeleton
- `systemd/timer.unit`: timer unit skeleton
- `systemd/user-service.unit`: per-user service skeleton

## CI
- `ci/github_actions_min_permissions.yml`: minimal permissions template
- `ci/github_release_vars.env`: GitHub release/wrapper variable contract (shared refs, branch policy, release tags)
- `ci/gitlab_rules.yml`: baseline `rules` with read-only guard for `github/mcr/main|staging`
- `ci/bitwarden_bws_env.sh`: validate/export `BWS_ACCESS_TOKEN` and `BWS_PROJECT_ID`
- `ci/gitlab_delivery_vars.env`: delivery variable contract (shared includes + release/patch vars)

## Containers
- `containers/Dockerfile`: rootless-friendly Dockerfile scaffold
- `containers/.dockerignore`: safe build context exclusions
- `containers/compose.yml`: Compose baseline (online)
- `containers/compose.offline.override.yml`: offline runtime override
- `containers/compose.rootful.override.yml`: root-in-container override
- `containers/compose.podman.override.yml`: Podman `userns_mode: keep-id` override
- `containers/.env.example`: safe env placeholders
- `containers/rootless_env.sh`: set UID/GID env vars for rootless compose

## auditd / logrotate / AIDE / CrowdSec
- `auditd/audit.rules`: minimal auditd rules
- `logrotate/app.logrotate`: logrotate example
- `aide/aide.conf`: AIDE baseline config
- `crowdsec/acquis.yaml`: CrowdSec log acquisition

## Terraform
- `terraform/versions.tf`: required versions
- `terraform/backend_remote.tf`: remote backend stub

## Ansible
- `ansible/ansible.cfg`: basic defaults
- `ansible/playbook.yml`: playbook skeleton

## Kubernetes
- `kubernetes/deployment.yaml`: deployment skeleton
- `kubernetes/service.yaml`: service skeleton

## Elastic Stack
- `elastic/elasticsearch.yml`: minimal elastic config
- `elastic/kibana.yml`: minimal kibana config
- `elastic/logstash.conf`: logstash pipeline skeleton

## Proxmox / libvirt
- `proxmox/storage.cfg`: storage config example
- `virsh/domain.xml`: libvirt domain skeleton

## System hardening
- `system/kernel-config.fragment`: kernel config fragment
- `system/grub-default`: GRUB default snippet
- `system/sysctl.conf`: sysctl baseline
- `system/usbguard.rules`: USBGuard rules example

## Docs / process
- `$CODEX_HOME/snippets/docs/pr_description.md`: PR description template
- `$CODEX_HOME/snippets/docs/prompt_contract.md`: prompt command contract skeleton

## Virtualization
- `virtualization/preseed_boot_params.txt`: Debian installer boot parameters (preseed)

## Debian preseed
- `preseed/include.preseed.cfg`: include file example
- `preseed/partman-btrfs.preseed.cfg`: btrfs partition recipe
- `preseed/late-command.sh`: late‑command hook example

## VS Code
- `vscode/settings.json`: baseline VS Code settings
- `vscode/devcontainer.json`: minimal devcontainer config

## Web
- `web/html/index.html`: static HTML skeleton
- `web/htmx/index.html`: HTMX page skeleton

## Desktop / Wayland
- `desktop/desktop-entry.desktop`: `.desktop` launcher
- `desktop/librewolf.overrides.cfg`: LibreWolf overrides
- `desktop/labwc/rc.xml`: Labwc config snippet
- `desktop/waybar.jsonc`: Waybar config snippet
- `desktop/kanshi.conf`: Kanshi config snippet
- `desktop/swaylock.conf`: Swaylock config snippet
- `desktop/wofi.conf`: Wofi config snippet
- `desktop/greetd.toml`: Greetd config snippet
- `desktop/regreet.css`: ReGreet styling snippet
- `desktop/polkit-rule.js`: Polkit rule example

## Related
- Templates: `$CODEX_HOME/templates/`
- Docs: `$CODEX_HOME/docs/`
- Skills: configured skill roots
- Snippets plan: `$CODEX_HOME/plans/snippets-library.md`
- Entry point: `$CODEX_HOME/index/pack/snippets.md`
