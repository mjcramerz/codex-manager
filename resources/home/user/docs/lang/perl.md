# Perl
Purpose: guide Perl work in Codex hook/runtime modules, installer helpers, and safe text/config transforms for the Codex coding agent.
You must read only the smallest section that resolves the current task, follow the first matching route, and stop broad browsing once the next concrete file or command is clear.

## Use this guide when
- editing `$CODEX_HOME/hooks/scripts/lib/Codex/Hook/**`
- writing small deterministic Perl helpers for install or runtime tasks
- reviewing Perl code that touches hooks, JSON payloads, or config rendering

## Baseline
- Enable `strict` and `warnings` by default.
- You must keep side effects at the boundary; keep parsing and rendering functions testable.
- You must prefer explicit data validation for hook payloads and user-controlled input.
- Avoid shell-outs when Perl built-ins or modules can do the job safely.

## Validation
- Syntax check: `perl -c path/to/file.pm`
- Test suite: `prove -lr t` or the repo-local equivalent when present
- Config/output validation: reparse generated JSON/TOML/YAML after mutation

## After that, you must check related files
- `$CODEX_HOME/docs/style/perl.md`
- `$CODEX_HOME/docs/workflows/codex-manager.md`
- `$CODEX_HOME/templates/perl/codex-hook-module/`
- `$CODEX_HOME/index/domains/lang/perl.md`
