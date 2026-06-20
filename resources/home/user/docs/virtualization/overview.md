# Virtualization overview
Purpose: route VM-centric work to the right stack: libvirt, virsh, Vagrant, Proxmox, or unattended Debian install flows.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Choose one path
- Unattended Debian install flow -> `debian-preseed.md`
- Local VM stack -> `qemu-kvm-libvirt.md`
- CLI VM operations -> `virsh.md`
- Repeatable dev VMs -> `vagrant-libvirt.md`
- Clustered VM management -> `proxmox.md`

## Defaults
- Prefer read-only inspection before privileged host mutation.
- Keep network mode explicit: NAT, bridged, or isolated.
- Treat provisioning scripts and seed files as high-impact inputs.

## Related
- `$CODEX_HOME/docs/workflows/debian-preseed.md`
- `$CODEX_HOME/docs/workflows/proxmox.md`
- `$CODEX_HOME/docs/workflows/virsh.md`
- `../containers/overview.md`
