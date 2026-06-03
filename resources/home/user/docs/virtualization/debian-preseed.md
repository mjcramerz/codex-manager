# Debian preseed (deep dive)
Guidance for split‑file preseeds and unattended installs.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/virtualization/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Structure
- `preseed.cfg` (top‑level, includes others)
- `preseed/account.preseed.cfg`
- `preseed/network.preseed.cfg`
- `preseed/apt.preseed.cfg`
- `preseed/partman.preseed.cfg`
- `preseed/packages.preseed.cfg`
- `preseed/finish.preseed.cfg` (optional late command)

## Baseline practices
- Never include plaintext passwords; use crypt(3) hashes.
- Always test in a VM before hardware installs.
- Keep destructive options explicit and documented.
- Host over HTTPS when possible.

## Late commands
Use `preseed/late_command` sparingly:
- Fetch a minimal script and run `in-target`.
- Avoid long‑running provisioning in the installer environment.
- Log outputs to a known path for debugging.

## Validation checklist
- Confirm disk target and partitioning recipe.
- Verify mirror URLs and connectivity.
- Boot a VM and validate hostname, network, packages, and bootloader.

See also:
- `../workflows/debian-preseed.md`
- `../workflows/overview.md`
- `$CODEX_HOME/templates/virtualization/debian-preseed/`
- Use skill os-debian-preseed.
- `$CODEX_HOME/snippets/preseed/include.preseed.cfg`
- `$CODEX_HOME/index/domains/system/debian-preseed.md`
