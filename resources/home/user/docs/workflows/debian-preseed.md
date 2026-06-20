# Debian preseed workflow

Start with `$CODEX_HOME/plans/workflows/workflow-debian-preseed.md` before executing this workflow.
Purpose: guide unattended Debian installation work, with concrete alignment to the `debian-preseed-di` repository.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/workflows/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Plan
- Start from the linked workflow plan template above, then tailor scope, constraints, and validation commands before editing.
- Keep the plan updated as execution progresses, including risk and rollback notes for any sensitive change.

## Repo anchors
- `/data/workspace/gitlab/computes/active/debian-preseed-di/README.md`
- `d-i/debian/preseed.cfg`
- `d-i/debian/classes/**`
- `d-i/debian/hosts/profiles/**`
- `d-i/debian/scripts/**`

## Safety first
- Preseed can wipe disks. Always validate in a VM before real hardware.
- Keep preseed files under version control but never store plaintext passwords.
- Use HTTPS for hosted preseeds and restrict access where possible.

## Core settings checklist
- Locale, keyboard, timezone
- Network (DHCP vs static)
- Mirror configuration
- Partitioning strategy and confirmation flags
- User creation and password hash
- Package selection and upgrades
- Bootloader target and reboot behavior

## Passwords
- Use `passwd/user-password-crypted` with a strong hash.
- Store the hash in a secrets manager or inject it at build time.

## Usage pattern
1) Host the preseed file (local HTTP, HTTPS, or initrd).
2) Boot the installer with:
   - `auto=true`
   - `priority=critical`
   - `preseed/url=...` or `preseed/file=...`
3) Validate post-install state with a script or smoke tests.

## Repo-specific contract
- Keep storage, class-selection, and late-command behavior grounded in the tracked repo contracts.
- Treat kernel command-line inputs as untrusted and validate shape early.
- Keep secrets out of tracked seeds; prefer deployment-time injection for sensitive values.
- Re-test both happy-path and failure-path boot/install behavior after material preseed changes.

## Split‑file approach (recommended)
- Keep `preseed.cfg` minimal and include split seeds.
- Separate account, network, apt, and partman settings.
- Review only the seed you change; reduce risk.

## High‑risk flags
- Disk target (`partman-auto/disk`) must be explicit.
- Confirmation flags must match the intended destructive actions.

## Template
- `$CODEX_HOME/templates/virtualization/debian-preseed/`

## Security checkpoints
- Use hashed credentials only and protect hosted preseed delivery with access controls.
- Pin destructive disk targets explicitly (`partman-auto/disk`) for each hardware class.
- Treat late-command assets as sensitive and rotate bootstrap secrets after install.

## Testing checkpoints
- Run unattended installs in VMs that match BIOS/UEFI modes used in production.
- Verify partition layout, account policy, package set, and bootloader state post-install.
- Test failure paths (unreachable mirror or preseed URL) and confirm recovery behavior.

## Deployment checkpoints
- Gate physical rollout on a validated preseed revision and golden image checksum.
- Keep prior preseed revision and boot params for rollback in provisioning systems.
- Stage rollout by hardware baseline and archive installer logs per batch.

## Multi-agent handoff
- Coordinator defines hardware matrix, destructive flags, and required approvals.
- Executor publishes preseed revision, boot parameters, and post-install evidence.
- Receiver tracks field results and opens drift fixes for any baseline mismatch.
## Related
- `overview.md`
- `../virtualization/debian-preseed.md`
- Use skill `os-debian-preseed`.
- `$CODEX_HOME/snippets/virtualization/preseed_boot_params.txt`
- `$CODEX_HOME/snippets/preseed/include.preseed.cfg`
- `../virtualization/overview.md`
- `$CODEX_HOME/index/pack/workflows.md`
- `$CODEX_HOME/index/domains/system/debian-preseed.md`
