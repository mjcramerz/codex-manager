# Shell runtime guidance
Purpose: define the common shell execution rules for shell-sensitive work in the runtime pack.

## Choose the matching shell
- Use `zsh` for zsh-sensitive commands and zsh assets.
- Use `bash` for Bash-sensitive commands and Bash assets.
- Use `sh`/`dash` for POSIX-portable assets.
- Validate shell-specific files with the shell they claim to support.

## Deterministic execution defaults
- Prefer `LC_ALL=C` and `TZ=UTC` for reproducible command output.
- Prefer machine-readable flags (`--json`, `--porcelain`, `--null`, `--color=never`) when available.
- Prefer read-only discovery first, then the smallest deterministic change.
- Avoid interactive flows and fuzzy parsing.

## Safe command shape
- Refuse destructive operations on empty paths, `/`, or ambiguous globs.
- Use `--` before untrusted positionals where supported.
- Prefer explicit arrays or direct argv execution over shell-string construction.
- Reparse structured files after mutation.

## Documentation scope
- Keep shell guidance focused on shell choice, reproducibility, validation, and command safety.
- Route plugin, skill, and workflow ownership questions through the matching pack entrypoints instead of shell guidance.

## Related
- `$CODEX_HOME/docs/style/bash.md`
- `$CODEX_HOME/docs/style/sh.md`
- `$CODEX_HOME/index/style/overview.md`
