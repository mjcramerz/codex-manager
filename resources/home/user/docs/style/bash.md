# Bash style guide
Canonical Bash guidance for this pack. Follow repo-specific conventions first.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/style/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Baseline: strict mode
Use strict mode for any non-trivial script:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
```

Prefer the hardened snippet: `$CODEX_HOME/snippets/bash/strict.sh`.
If `$CODEX_HOME/AGENTS.md` confirms the active session is Bash, read `$CODEX_HOME/UNIX.md` before using this deeper style guide.

## Input handling
- Treat **all inputs as untrusted**: CLI args, env vars, files, git output, network responses.
- Validate and normalize early (required flags, mutually exclusive options, path sanity).
- Use `--` to separate flags from positionals; reject unknown flags.
- Prefer explicit allowlists (subcommands, modes, file extensions) over implicit behavior.

## Subprocess safety
- **Never** build shell strings with untrusted input (avoid `bash -lc`, `sh -c`, `eval`).
- Prefer exec-arg APIs and arrays:
  - `cmd=(rg --fixed-string -- "$pattern" "$path"); "${cmd[@]}"`
- Set timeouts for network calls (or refuse network by default).

## Filesystem safety
- Refuse dangerous paths (`""`, `/`, `.` when destructive).
- Prefer `mktemp -d` + `trap` cleanup; avoid predictable temp names.
- Avoid TOCTOU when writing: write to temp + atomic rename where feasible.
- Avoid following indirect path aliases when writing if the path is attacker-controlled.

## Output and logging
- **stdout**: machine-readable output (JSON, newline-delimited values).
- **stderr**: human logs (`INFO/WARN/ERROR`, timestamps).
- Provide `--dry-run` for scripts that mutate state.

Prefer the hardened snippet: `$CODEX_HOME/snippets/bash/logging.sh`.

## Portability
- Declare bash explicitly; do not rely on `/bin/sh` behavior.
- Watch for BSD vs GNU differences (`sed`, `date`, `stat`).
- If you must rely on GNU behavior, detect platform and fail with a clear message.

## Linting
- Run `shellcheck` on scripts and treat new warnings as failures.
- Keep scripts shellcheck-clean or document specific disables with comments.

## References
- `overview.md`
- Snippets: `$CODEX_HOME/snippets/bash/`
- Skill: Use skill shell-bash.
- Template: `$CODEX_HOME/templates/bash/script-skeleton/`
- `$CODEX_HOME/index/pack/style.md`
- `$CODEX_HOME/index/style/bash.md`
