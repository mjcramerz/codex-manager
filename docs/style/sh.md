# POSIX/BusyBox sh style guide
This guide targets `/bin/sh`, BusyBox `ash`, `dash`, and other POSIX shells.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/style/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Baseline
- Use `#!/bin/sh` and avoid bashisms (`[[ ]]`, arrays, brace expansion, `$'...'`, process substitution).
- Quote variable expansions unless you explicitly need word splitting or globbing.
- Prefer `printf` over `echo -e`.
- Use `command -v` for dependency checks.
- Prefer `getopts` for flags; avoid non-POSIX `getopt`.

## Strict mode
```
set -eu
(set -o pipefail 2>/dev/null) || true
IFS=$(printf '\n\t')
```

Notes:
- `pipefail` is not POSIX; guard it as shown.
- `set -e` does not trigger on every failure. Use explicit checks where needed.

## Functions and flow
- Define functions as `name() { ...; }` and avoid `function` keyword.
- Use `case` for branching; avoid regex-heavy `expr` or `grep` when possible.
- Use `trap` for cleanup (`EXIT`, `INT`, `TERM`), not `ERR`.

## Files and temp paths
- Use `umask 077` before writing secrets or private keys.
- Prefer `mktemp` when available and verify it exists; fall back only when necessary.
- Avoid writing into world-writable locations without randomness.

## Portability checklist
- No `[[ ]]`, `local`, `source`, or arithmetic arrays.
- No `read -a`, `mapfile`, or process substitution.
- Use `IFS= read -r` when reading lines.
- Avoid `sed -r` or `grep -P`; stick to POSIX flags.

See also:
- `overview.md`
- `$CODEX_HOME/snippets/sh/`
- Use skill shell-sh.
- `$CODEX_HOME/templates/sh/posix-sh-script/`
- `$CODEX_HOME/index/pack/style.md`
- `$CODEX_HOME/index/style/sh.md`
