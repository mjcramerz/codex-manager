---
title: AGENTS.md (sanitized operating contract)
status: active
owner: Matthew Cramer
tags:
- home
- agents-md
- agents
updated: '2026-03-04'
---
# AGENTS.md (sanitized operating contract)

This contract applies to this tree and child paths unless a deeper `AGENTS.md` overrides it.

## Priorities
1) Correctness
2) Security
3) Performance
4) Maintainability
5) Polish

## Scope and hierarchy
- Authority order: system -> developer -> user -> this file -> deeper instructions.
- Preserve behavior unless a request explicitly changes behavior.
- Keep diffs minimal, reviewable, and deterministic.
- Apply all active instruction files for each touched path.
- When the task targets shell assets or shell runtime behavior, load the matching shell skill (`shell-bash`, `shell-zsh`, or `shell-sh`); when it targets repo automation or git delivery controls, load `repo-ops`.

## Core rules
- Treat inputs as untrusted; validate shape, size, and ranges.
- Use bounded retries/timeouts for network and I/O.
- Avoid destructive operations unless explicitly requested and acknowledged.
- Do not add compatibility branches or legacy toggles without explicit request.
- Fallback behavior is only allowed when the user explicitly requests it.
- Keep secrets out of logs and avoid dumping environment values.
- Prefer deterministic commands and explicit formats.
- For shell-sensitive work, use the shell guide already selected by the surrounding session contract and explicitly invoke that matching shell when running commands.
- Read `$CODEX_HOME/UNIX.md` and explicitly invoke the matching shell for shell-sensitive commands.
- Keep shell-specific assets honest: Bash assets stay Bash-only, and shared shell assets must be validated in the supported runtimes.
- Avoid machine-specific project references in user-facing guidance.
- Runtime-home docs, prompts, templates, snippets, and plans must refer only to installed runtime paths such as `$CODEX_HOME`, `$CODEX_SKILLS`, and the managed runtime/admin directories; do not point back into the installer repository.

## Branch and workflow policy
- Use `mcr/*` branches for implementation work.
- Fetch and prune remotes before branch operations.
- Keep protected promotion flow in order: `mcr/main -> mcr/staging -> mcr/release`.
- Keep working trees auditable and isolated.

## Routing protocol
1) Read the active AGENTS contract.
2) Read `$CODEX_HOME/INDEX.md` and select one entrypoint.
3) Load only the minimum skill(s) needed for the request.
4) Use `$CODEX_HOME/UNIX.md`.
5) Explicitly invoke the matching shell for shell-sensitive commands.
6) Open deeper docs only when the selected entrypoint requires them.

## Runtime layout reminders
- Runtime plugin marketplace metadata lives at `$CODEX_HOME/.agents/plugins/marketplace.json`.
- Runtime plugin bundles live under `$CODEX_HOME/plugins/cache/<marketplace>/<plugin>/local/`.
- Shared runtime skills live under `$CODEX_SKILLS/**` and the managed admin skill root.
- Installed instruction assets live under the managed runtime instructions directory.

## Tooling discipline
- Prefer read-only discovery first, then minimal edits.
- Prefer `rg`/`rg --files` for search.
- Use `apply_patch` for focused single-file edits.
- Use deterministic scripts for broad, repeated changes.
- When editing shell-facing scripts, snippets, templates, or startup files, preserve shebang/runtime alignment and validate with the matching shell entrypoint.

## Testing and verification
- Run the narrowest tests/build checks that prove the change.
- Validate error paths, auth boundaries, and timeout behavior when relevant.
- If checks are skipped, explain why and list what should run next.

## Output expectations
- Provide: Summary -> Tests -> Risks/TODOs -> Next steps.
- Include concrete file references with line numbers for key edits.
- State assumptions explicitly when behavior depends on permissions or credentials.
