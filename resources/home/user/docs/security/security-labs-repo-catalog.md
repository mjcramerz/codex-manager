# Security source catalog
Authoritative source set for security operations workflows.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/security/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Purpose
Use this catalog for current documentation and standards while preparing NetHunter, mobile rooting, and defensive simulation runbooks.

## Retrieval channels
- Preferred: Fetch MCP + Context7 MCP for source refresh and citation.
- Current runtime fallback (2026-02-13 UTC): Context7 + web lookups, because Fetch MCP returned `SIGSYS` on `npm version`.

## Kali NetHunter (official)
- Building NetHunter:
  - https://www.kali.org/docs/nethunter/building-nethunter/
- Porting NetHunter with kernel builder:
  - https://www.kali.org/docs/nethunter/porting-nethunter-kernel-builder/
- Porting NetHunter (manual path):
  - https://www.kali.org/docs/nethunter/porting-nethunter/
- Kernel patching workflow:
  - https://www.kali.org/docs/nethunter/nethunter-kernel-1-patching/
- Build scripts (upstream GitLab):
  - https://gitlab.com/kalilinux/nethunter/build-scripts/kali-nethunter-kernel-builder
  - https://gitlab.com/kalilinux/nethunter/build-scripts/kali-nethunter-installer

## Android platform (official)
- Bootloader locking/unlocking model:
  - https://source.android.com/docs/core/architecture/bootloader/locking_unlocking
- Fastboot / fastbootd architecture:
  - https://source.android.com/docs/core/architecture/bootloader/fastbootd
- GKI release/build guidance:
  - https://source.android.com/docs/core/architecture/kernel/gki-releases
- Android SDK Platform-Tools release notes (`adb`, `fastboot`):
  - https://developer.android.com/tools/releases/platform-tools

## Defensive standards and mappings
- MITRE ATT&CK:
  - https://attack.mitre.org/
- NIST SP 800-115 (technical testing guide):
  - https://csrc.nist.gov/publications/detail/sp/800-115/final
- NIST SP 800-153 (wireless/mobile guidance):
  - https://csrc.nist.gov/publications/detail/sp/800-153/final
- CISA mobile security resources:
  - https://www.cisa.gov/resources-tools/resources/mobile-security-best-practices

## Usage notes
1) Start from official documentation and standards before applying internal playbooks.
2) Record exact URL, retrieval date (UTC), and commit/tag when consuming build guidance.
3) Keep local mirror paths out of published runbooks; use environment variables for workspace-local clones.
4) Re-validate critical procedures when upstream docs or platform-tools versions change.

## Exclusions
- Do not use uncontrolled PoC instructions as primary guidance.
- Do not run unvetted exploit code during kernel/rooting workflows.
- Do not execute actions outside the documented scope manifest.
