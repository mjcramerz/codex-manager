# Secrets handling
- Do not commit secrets.
- Prefer environment variables or a secrets manager.
- Never log secrets.
- Redact sensitive values in error paths.
- For local dev, use `.env` but keep it out of git.
- Rotate credentials regularly and design for rotation (short-lived tokens where possible).
- Apply least privilege: scoped tokens, minimal IAM permissions.
- For CI, prefer a dedicated secrets manager (e.g., Bitwarden Secrets Manager).
- For local hosts, prefer keyring-backed storage and retrieval patterns (`bitwarden-secrets-local.md`).
- Store private keys in a secrets manager; see `key-management.md`.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/security/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


Patterns:
- Python: load via pydantic-settings; validate at startup.
- Rust: load via env + typed config; fail-fast on missing required secrets.

## CI/CD notes
- Keep workflow permissions minimal and avoid long-lived deploy keys.
- Prefer OIDC (`id-token: write`) to exchange for short-lived cloud creds when supported.
- Do not print environment dumps in CI logs.
- Add secret scanning in CI when available.

See also:
- `overview.md`
- `bitwarden-secrets.md`
- `bitwarden-secrets-local.md`
- `key-management.md`
- `../workflows/ci-cd.md`
- `$CODEX_HOME/index/core/security.md`
