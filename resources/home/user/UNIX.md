# UNIX compatibility entrypoint
Purpose: keep the historical `$CODEX_HOME/UNIX.md` path valid while routing shell-sensitive work to the newer shell guidance.

## Required order
1. `$CODEX_HOME/AGENTS.md`
2. `$CODEX_HOME/memories/MEMORY.md` when the task is repo-aware or ambiguous
3. `$CODEX_HOME/INDEX.md`
4. `$CODEX_HOME/index/pack/plans.md` and `$CODEX_HOME/index/pack/workflows.md`
5. `$CODEX_HOME/index/pack/skills.md`
6. `$CODEX_HOME/UNIX.md`

## Canonical shell docs
- Shell execution baseline: `$CODEX_HOME/docs/style/shell-runtime.md`
- Bash conventions: `$CODEX_HOME/docs/style/bash.md`
- POSIX sh conventions: `$CODEX_HOME/docs/style/sh.md`
- Perl conventions for hook/runtime code: `$CODEX_HOME/docs/style/perl.md`
- Rust conventions for cargo-driven repos: `$CODEX_HOME/docs/style/rust.md`

## Runtime-state guardrails
- Treat `$CODEX_HOME/sessions/`, `$CODEX_HOME/shell_snapshots/`, and `$CODEX_HOME/.credentials.json` as runtime-only.
- Do not copy those artifacts into source-controlled pack docs or templates.

## Why this file stays small
The old monolithic command catalog was retired. Keep this path as a stable router, and move detailed shell guidance into the style docs above.
