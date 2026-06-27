# auditd
Guidance for Linux auditd rules and safe logging.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/observability/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Baseline practices
- Start small: capture authentication, privilege escalation, and key system files.
- Prefer explicit allowlists of paths and syscalls over wide, noisy rules.
- Keep logs immutable and permission‑locked (`600` root).
- Rotate and ship audit logs off‑host when feasible.

## Rule strategy
- Track identity: `user`, `group`, `sudo`, `ssh`, `pam` changes.
- Track integrity: `/etc`, `/usr/local`, bootloader config, kernel modules.
- Track time changes and auditd configuration changes.
- Avoid high‑volume rules without rate limits; review event volume first.

## Operations
- Validate rules with `augenrules --check` where supported.
- Test in a VM or staging host before broad rollout.
- Keep a rollback plan (restore previous rules, restart auditd).

See also:
- `overview.md`
- `$CODEX_HOME/templates/observability/auditd-rules-skeleton/`
- `$CODEX_HOME/snippets/auditd/audit.rules`
- `../workflows/auditd.md`
- Use skill secops-auditd.
- `$CODEX_HOME/index/domains/observability/stack.md`
- `$CODEX_HOME/index/domains/observability/auditd.md`
