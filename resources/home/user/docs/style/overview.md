# Style guides
Follow repository-local conventions first. Use this pack as defaults when a repo has no explicit style guide.


## Contents
<!-- BEGIN:contents -->
- `$CODEX_HOME/docs/style/bash.md` — Bash style guide
- `$CODEX_HOME/docs/style/go.md` — Go style guide
- `$CODEX_HOME/docs/style/python.md` — Python style guide
- `$CODEX_HOME/docs/style/rust.md` — Rust style guide
- `$CODEX_HOME/docs/style/sh.md` — POSIX/BusyBox sh style guide
- `$CODEX_HOME/docs/style/typescript.md` — TypeScript style guide
<!-- END:contents -->


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Shell session guides
- Bash session: `$CODEX_HOME/UNIX.md` -> `bash.md` -> `$CODEX_HOME/snippets/bash/`

## Language guides
- Bash: `bash.md` + `$CODEX_HOME/snippets/bash/`
- POSIX sh: `sh.md` + `$CODEX_HOME/snippets/sh/`
- Python: `python.md` + `$CODEX_HOME/snippets/python/`
- Rust: `rust.md` + `$CODEX_HOME/snippets/rust/`
- Go: `go.md` + `$CODEX_HOME/snippets/go/`
- TypeScript: `typescript.md` + `$CODEX_HOME/snippets/typescript/`

See also: top-level entrypoint `$CODEX_HOME/index/pack/style.md`.
Templates: `$CODEX_HOME/templates/bash/` and `$CODEX_HOME/templates/sh/`.
Entry points: `$CODEX_HOME/index/pack/templates.md`, `$CODEX_HOME/index/pack/snippets.md`.

## Cross-language conventions
- Prefer small, cohesive diffs; avoid drive-by refactors.
- Keep I/O at the edges; keep core logic testable and deterministic.
- Never log secrets. Prefer structured logs to stderr.
- Bound all I/O (timeouts) and resource usage (size limits, concurrency limits).
- Treat external inputs as hostile (args/env/files/network/UI/DB).

## Documentation style
- Explain *why* when intent is not obvious; avoid redundant comments.
- Prefer short examples in $CODEX_HOME/snippets/ over long narrative.
