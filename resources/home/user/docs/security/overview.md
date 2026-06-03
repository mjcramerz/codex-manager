# Security overview
Security is a product feature. This pack assumes:
- inputs are hostile
- dependencies may be compromised
- CI can be attacked
- logs leak data if you let them


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Start here
- Code review hardening checklist: `review-hardening.md`
- Threat modeling: `threat-model.md`
- Secrets: `secrets.md`
- Key management: `key-management.md`
- Bitwarden Secrets Manager (local hosts): `bitwarden-secrets-local.md`
- Bitwarden Secrets Manager: `bitwarden-secrets.md`
- Logging hygiene: `logging.md`
- Supply-chain controls: `supply-chain-controls.md`
- NetHunter Pixel 9a reference: `nethunter-pixel9a.md`
- OffSec defense reference: `offsec-defense.md`
- Security operations index: `security-labs-index.md`
- Security source catalog: `security-labs-repo-catalog.md`
- Security tool guides: `security-labs-tool-guides.md`
- Web hardening defaults: `web-hardening.md`
See `../workflows/overview.md` for related workflows.


## Contents
<!-- BEGIN:contents -->
- `$CODEX_HOME/docs/security/bitwarden-secrets-local.md` — Bitwarden Secrets Manager (BWS) for local hosts
- `$CODEX_HOME/docs/security/bitwarden-secrets.md` — Bitwarden Secrets Manager (BWS)
- `$CODEX_HOME/docs/security/key-management.md` — Key management (TLS, SSH, GPG)
- `$CODEX_HOME/docs/security/logging.md` — Logging policy
- `$CODEX_HOME/docs/security/review-hardening.md` — Review hardening checklist
- `$CODEX_HOME/docs/security/secrets.md` — Secrets handling
- `$CODEX_HOME/docs/security/nethunter-pixel9a.md` — NetHunter Pixel 9a reference
- `$CODEX_HOME/docs/security/offsec-defense.md` — OffSec defense reference
- `$CODEX_HOME/docs/security/security-labs-index.md` — Security operations index
- `$CODEX_HOME/docs/security/security-labs-repo-catalog.md` — Security source catalog
- `$CODEX_HOME/docs/security/security-labs-tool-guides.md` — Security tool guides
- `$CODEX_HOME/docs/security/supply-chain-controls.md` — Supply-chain controls (deeper checklist)
- `$CODEX_HOME/docs/security/supply-chain.md` — Supply-chain controls
- `$CODEX_HOME/docs/security/threat-model.md` — Threat modeling (lightweight)
- `$CODEX_HOME/docs/security/web-hardening.md` — Web hardening quick reference
<!-- END:contents -->

## Default expectations (baseline)
- Validate and bound inputs at trust boundaries (size limits, ranges, allowlists).
- Timeouts on all I/O; bounded retries with backoff + jitter.
- Never log secrets/PII; avoid logging request bodies by default.
- Lock down dependency updates (pins/lockfiles) and add audits in CI.
- Prefer least privilege with sandboxed execution profiles, non-root containers, and minimal CI permissions.

## Containers & virtualization (baseline)
- Prefer rootless Docker/Podman when feasible.
- Containers should run as a non-root user by default (`USER`).
- Avoid `--privileged`, `--cap-add=ALL`, and mounting the Docker socket unless explicitly required and reviewed.
- Prefer disabling network for tests that don’t need it (`--network=none`) and make network use explicit.

See also:
- `../containers/overview.md`
- `../virtualization/overview.md`
- `$CODEX_HOME/index/core/security.md`
- Use skill appsec-hardening.
