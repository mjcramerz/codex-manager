---
title: AGENTS.md (runtime pack operating contract)
status: active
owner: Matthew Cramer
tags:
- home
- agents-md
- agents
updated: 2026-06-21
---
# Runtime pack operating contract
Purpose: define the operating contract for the installed runtime-home pack under `$CODEX_HOME/**`.

This contract applies to `$CODEX_HOME` and every child path unless a deeper `AGENTS.md` overrides it.

## Mission
- Keep the runtime-home source pack coherent, fast to route, and correct for the installed Codex layout.
- Treat `$CODEX_HOME/**` as runtime pack material, not as a scratch area or a runtime dump.
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
2) Load `$CODEX_HOME/memories/MEMORY.md` only when the task is repo-aware, ambiguous, or depends on prior decisions.
3) Route through `$CODEX_HOME/INDEX.md`.
4) Read `$CODEX_HOME/index/pack/plans.md` and `$CODEX_HOME/index/pack/workflows.md`.
5) Load only the minimum skills required.
6) Follow `$CODEX_HOME/docs/style/shell-runtime.md` before shell-sensitive work.
7) Open one concrete entrypoint, then stop broad browsing.

## Pack focus
- Keep agent guidance centered on stable installed surfaces:
  - `$CODEX_HOME/docs/**`
  - `$CODEX_HOME/index/**`
  - `$CODEX_HOME/plans/**`
  - `$CODEX_HOME/templates/**`
  - `$CODEX_HOME/snippets/**`
  - `$CODEX_HOME/rules/**`
  - `$CODEX_HOME/memories/MEMORY.md`
  - `$CODEX_HOME/plugins/cache/**`
  - `$CODEX_HOME/.agents/plugins/marketplace.json`
- Use installed runtime paths in user-facing guidance; do not teach from repository-source paths.

## Source-of-truth map
- `$CODEX_HOME/INDEX.md` is the top router for the runtime pack.
- `$CODEX_HOME/index/manifest.yml` is the routing metadata source for pack entrypoints and related-link intent.
- `$CODEX_HOME/memories/MEMORY.md` is the memory-entry router for repo-aware work.
- `$CODEX_HOME/docs/**` contains runtime documentation source.
- `$CODEX_HOME/plans/**` contains plan-template source.
- `$CODEX_HOME/templates/**` contains reusable scaffolds.
- `$CODEX_HOME/.models/**` contains model catalog and instruction-source assets referenced by runtime config.
- `$CODEX_HOME/docs/create-prompts.md` owns the prompt-file catalog and direct prompt-file references for this tree.

## Documentation and routing rules
- Keep top-level routing docs concise. Route first, dive deeper only when needed.
- Update cross-links in the same change when files move or canonical paths change.
- If a doc references a runtime path, verify that the path exists in the installed pack.
- Do not leave stale machine-specific repository references in user-facing guidance.
- Do not hardcode workstation-specific repository paths in docs, plans, or instruction assets.
- Do not leave unresolved placeholders in non-template docs, plans, or workflow guides.
- Prefer one canonical explanation for a concept instead of repeating it across multiple overview files.
- Keep `docs/style/shell-runtime.md` as the shell compatibility entrypoint and route language-specific detail into the deeper style guides.

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
- When touching governing pack files (`$CODEX_HOME/AGENTS.md`, `$CODEX_HOME/INDEX.md`, `$CODEX_HOME/docs/**`, `$CODEX_HOME/index/**`, `$CODEX_HOME/plans/**`, `$CODEX_HOME/templates/**`, `$CODEX_SKILLS/**`), also run focused contract checks for stale links or structural drift.
- If you skip a check, say exactly why and name the next command that should run.

## Output contract
- Return: Summary -> Tests -> Risks/Follow-ups -> Next steps.
- Include concrete file references with line numbers for the important edits.
- State assumptions explicitly when behavior depends on credentials, permissions, or optional runtime assets.
