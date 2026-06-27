# GRUB configuration
Guidance for editing GRUB defaults and kernel command line safely.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/system/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Baseline practices
- Edit `/etc/default/grub` and regenerate configs; do not edit `grub.cfg` directly.
- Keep a known‑good kernel entry for rollback.
- Document any custom kernel parameters.

## Safe workflow
1) Edit `/etc/default/grub`.
2) Validate syntax.
3) Regenerate GRUB config (`update-grub` or `grub-mkconfig`).
4) Reboot and verify.

## Kernel command line
- Keep flags minimal; each flag is an operational contract.
- Avoid disabling security protections without explicit approval.

See also:
- `overview.md`
- `../workflows/grub.md`
- `$CODEX_HOME/templates/system/grub-baseline/`
- `$CODEX_HOME/snippets/system/grub-default`
- Use skill infra-grub.
- `$CODEX_HOME/index/domains/system/hardening.md`
- `$CODEX_HOME/index/domains/system/grub.md`
