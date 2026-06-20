---
title: AGENTS.md (runtime pack operating contract)
status: active
owner: Matthew Cramer
tags:
- home
- agents-md
- agents
updated: 2026-06-20
---
# Runtime pack operating contract
Purpose: define the operating contract for the runtime-home source pack under `resources/home/user/**`.

This contract applies to `resources/home/user` and every child path unless a deeper `AGENTS.md` overrides it.

## Mission
- Keep the runtime-home source pack coherent, fast to route, and correct for the installed Codex layout.
- Treat `resources/home/user/**` as pack source material, not as a scratch area or a runtime dump.
- Prefer short, high-signal routing and operational guidance over encyclopedic overviews.

## Priorities
1) Correctness
2) Security
3) Performance
4) Maintainability
5) Polish

## Authority and scope
- Follow this order: system -> developer -> user -> this file -> deeper instructions.
- Preserve behavior unless the request explicitly changes behavior.
- Keep diffs minimal, reviewable, and deterministic.
- Apply every active instruction file for each touched path.

## Required operating order
1) Read the active `AGENTS.md`.
2) Load `$CODEX_HOME/memories/MEMORY.md` only when it exists and the task is repo-aware, ambiguous, or depends on prior decisions.
3) Route through `$CODEX_HOME/INDEX.md`.
4) Read `$CODEX_HOME/index/pack/plans.md` and `$CODEX_HOME/index/pack/workflows.md`.
5) Load only the minimum skills required.
6) Follow `$CODEX_HOME/docs/style/shell-runtime.md` before shell-sensitive work.
7) Open one concrete entrypoint, then stop broad browsing.

## Runtime-state boundary
- Runtime state is target-only and must never sync back into this repo.
- Runtime-only artifacts must never be treated as pack source:
  - `$CODEX_HOME/memories/`
  - `$CODEX_HOME/sessions/`
  - `$CODEX_HOME/shell_snapshots/`
  - `$CODEX_HOME/.credentials.json`
  - `history.jsonl`
  - `session_index.jsonl`
  - `version.json`
  - `.personality_migration`

## Source-of-truth map
- `resources/home/user/INDEX.md` is the top router for the runtime pack.
- `resources/home/user/index/manifest.yml` is the routing metadata source for index entrypoints and related-link intent.
- `resources/home/user/docs/**` contains runtime documentation source.
- `resources/home/user/plans/**` contains plan-template source.
- `resources/home/user/templates/**` contains reusable scaffolds.
- `resources/home/user/.models/**` contains model catalog and instruction-source assets referenced by runtime config.
- `resources/home/user/docs/create-prompts.md` owns the prompt-file catalog and direct prompt-file references for this tree.

## Documentation and routing rules
- Keep top-level routing docs concise. Route first, dive deeper only when needed.
- Update cross-links in the same change when files move or canonical paths change.
- If a doc references a runtime path, verify that the path exists in the current source pack or clearly mark it runtime-only.
- Do not leave stale machine-specific repository references in user-facing guidance.
- Do not hardcode workstation-specific repository paths in docs, plans, or instruction assets.
- Do not leave unresolved placeholders in non-template docs, plans, or workflow guides.
- Prefer one canonical explanation for a concept instead of repeating it across multiple overview files.
- Keep shell guidance routed directly through `docs/style/shell-runtime.md` and the language-specific style guides.

## Structured-format rules
- Validate shape, size, and ranges for untrusted inputs.
- Re-parse edited JSON, YAML, and TOML before finishing the turn.
- Keep comments out of files that claim to be strict JSON.
- Keep generated marker blocks (`BEGIN` / `END`) syntactically intact when editing surrounding text.

## Editing discipline
- Prefer `rg` / `rg --files` for discovery.
- Use `apply_patch` for focused manual edits.
- Use deterministic scripts only when broad repetition makes them safer than manual patching.
- Do not invent fallback paths, compatibility branches, or legacy toggles unless explicitly requested.

## Validation requirements
- Run the narrowest checks that prove the change.
- When touching governing pack files (`AGENTS.md`, `INDEX.md`, `docs/**`, `index/**`, `plans/**`, `templates/**`, `resources/skills/**`), also run focused contract checks for stale links or structural drift.
- If you skip a check, say exactly why and name the next command that should run.

## Output contract
- Return: Summary -> Tests -> Risks/Follow-ups -> Next steps.
- Include concrete file references with line numbers for the important edits.
- State assumptions explicitly when behavior depends on credentials, permissions, or optional runtime assets.
