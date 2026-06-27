# Proxmox VE
Guidance for Proxmox virtualization setups.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/virtualization/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Baseline practices
- Treat storage layout as high‑risk; plan before creating pools.
- Prefer templates and clones for repeatable VM creation.
- Keep backups and verify restore workflows.

## Storage notes
- Common backends: ZFS, LVM-thin, directory.
- Keep `storage.cfg` under version control (where safe).

## Networking
- Use explicit bridges; document VLANs and firewall rules.

See also:
- `overview.md`
- `../filesystems/proxmox.md`
- `$CODEX_HOME/templates/virtualization/proxmox-vm-skeleton/`
- `$CODEX_HOME/snippets/proxmox/storage.cfg`
- Use skill infra-proxmox.
- `$CODEX_HOME/index/domains/infra/virtualization.md`
- `$CODEX_HOME/index/domains/infra/proxmox.md`
