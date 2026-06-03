# Virtualization overview
This pack supports a “reproducible environments” mindset: when in doubt, prefer running risky or dependency-heavy workflows inside containers or VMs.


## Contents
<!-- BEGIN:contents -->
- `$CODEX_HOME/docs/virtualization/debian-preseed.md` — Debian preseed (deep dive)
- `$CODEX_HOME/docs/virtualization/proxmox.md` — Proxmox VE
- `$CODEX_HOME/docs/virtualization/qemu-kvm-libvirt.md` — QEMU/KVM + libvirt
- `$CODEX_HOME/docs/virtualization/vagrant-libvirt.md` — Vagrant (libvirt)
- `$CODEX_HOME/docs/virtualization/virsh.md` — virsh / libvirt
<!-- END:contents -->


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Tools covered
- **QEMU/KVM + libvirt**: standard Linux virtualization stack for local VMs.
- **Vagrant**: reproducible VM environments (including with the libvirt provider).
- **Debian preseed**: unattended OS installs for VMs or bare metal.
- **Proxmox VE**: VM management and storage for homelab/prod clusters.

## Security posture
- Treat VM/host provisioning as high-impact: changes are often privileged and persistent.
- Prefer read-only inspection first (status, config dumps) before making host changes.
- Make network access explicit: NAT vs bridged vs isolated networks.

## When to choose VMs
- You need kernel-level isolation or a different OS kernel.
- You need to reproduce low-level system behavior not captured by containers.
- You want a hermetic environment with controlled networking.

- Template: `$CODEX_HOME/templates/virtualization/vagrant-libvirt-skeleton/`
- Template: `$CODEX_HOME/templates/virtualization/debian-preseed/`
- Skill: Use skill infra-virtualization.

See also:
- `qemu-kvm-libvirt.md`
- `vagrant-libvirt.md`
- `proxmox.md`
- `virsh.md`
- `../workflows/debian-preseed.md`
- `debian-preseed.md`
- `$CODEX_HOME/index/domains/system/debian-preseed.md`
- `../containers/overview.md`
- `$CODEX_HOME/index/domains/infra/virtualization.md`
- `$CODEX_HOME/index/pack/templates.md`
