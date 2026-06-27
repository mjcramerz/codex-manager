# Host hardening overview
Purpose: route OS-level boot, kernel, sysctl, optimization, and device-control work to the correct guide.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Scope
- Bootloader and kernel command-line changes
- Kernel build/config and module policy
- Sysctl tuning
- Performance/security tuning
- USB device control

## Guardrails
- Treat host changes as high-risk and rollback-sensitive.
- Validate in a VM or equivalent lab when feasible.
- Make one class of change at a time and verify it before layering more.

## Quick map
- GRUB: `grub.md`
- Kernel build/config: `kernel.md`
- sysctl tuning: `sysctl.md`
- Optimizations: `optimizations.md`
- USBGuard: `usbguard.md`
