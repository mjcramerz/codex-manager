# Host hardening overview
Guidance for OS‑level hardening and tuning.


## Contents
<!-- BEGIN:contents -->
- `$CODEX_HOME/docs/system/grub.md` — GRUB configuration
- `$CODEX_HOME/docs/system/kernel.md` — Kernel build & configuration
- `$CODEX_HOME/docs/system/optimizations.md` — Performance/security optimizations
- `$CODEX_HOME/docs/system/sysctl.md` — sysctl tuning
- `$CODEX_HOME/docs/system/usbguard.md` — USBGuard
<!-- END:contents -->


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Scope
- Kernel build/config and module policy
- Bootloader and kernel command line
- sysctl tuning and baseline security knobs
- USB device control (USBGuard)

## Safety baseline
- Treat host changes as high‑risk; validate in a VM first.
- Make changes incremental; test and measure after each change.
- Keep a rollback plan (previous kernel, previous GRUB config, revert sysctl).

## Quick map
- Kernel: `kernel.md`
- GRUB: `grub.md`
- sysctl: `sysctl.md`
- USBGuard: `usbguard.md`
- Optimizations: `optimizations.md`

See also:
- `../workflows/kernel-build.md`
- `../workflows/sysctl.md`
- `../workflows/usbguard.md`
- `$CODEX_HOME/index/domains/system/hardening.md`
- `$CODEX_HOME/index/domains/system/optimizations.md`
