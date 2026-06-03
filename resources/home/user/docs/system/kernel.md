# Kernel build & configuration
Guidance for building and configuring a custom kernel.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/system/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Baseline practices
- Start from the distro kernel config (`/boot/config-*`) and change minimally.
- Use config fragments for small deltas; keep them versioned.
- Verify build provenance (signatures) when downloading sources.
- Test new kernels in a VM before deploying to hosts.

## Build workflow (high‑level)
1) Obtain kernel source (distro or upstream).
2) Copy baseline config and run `olddefconfig`.
3) Apply config fragments and re‑run `olddefconfig`.
4) Build with reproducible settings and a pinned toolchain.
5) Install packages or modules; update bootloader.
6) Keep the previous kernel bootable for rollback.

## Config hygiene
- Disable unused subsystems to reduce attack surface.
- Enable module signature verification where policy requires it.
- Prefer LTS kernels for stability.

See also:
- `overview.md`
- `../workflows/kernel-build.md`
- `$CODEX_HOME/templates/system/kernel-build-skeleton/`
- `$CODEX_HOME/snippets/system/kernel-config.fragment`
- Use skill infra-kernel.
- `$CODEX_HOME/index/domains/system/hardening.md`
- `$CODEX_HOME/index/domains/system/kernel.md`
