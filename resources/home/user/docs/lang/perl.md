# Perl
Purpose: guide Perl work in Codex hook/runtime modules, installer helpers, and safe text/config transforms.

## Use this guide when
- editing `$CODEX_HOME/hooks/scripts/lib/Codex/Hook/**`
- writing small deterministic Perl helpers for install or runtime tasks
- reviewing Perl code that touches hooks, JSON payloads, or config rendering

## Baseline
- Enable `strict` and `warnings` by default.
- Keep side effects at the boundary; keep parsing and rendering functions testable.
- Prefer explicit data validation for hook payloads and user-controlled input.
- Avoid shell-outs when Perl built-ins or modules can do the job safely.

## Validation
- Syntax check: `perl -c path/to/file.pm`
- Test suite: `prove -lr t` or the repo-local equivalent when present
- Config/output validation: reparse generated JSON/TOML/YAML after mutation

## Related
- `$CODEX_HOME/docs/style/perl.md`
- `$CODEX_HOME/docs/workflows/codex-manager.md`
- `$CODEX_HOME/templates/perl/codex-hook-module/`
- `$CODEX_HOME/index/domains/lang/perl.md`
