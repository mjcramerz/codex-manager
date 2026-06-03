---
title: AGENTS.md (runtime pack operating contract)
status: active
owner: Matthew Cramer
tags:
- home
- agents-md
- agents
updated: '2026-06-03'
---
# Runtime pack operating contract
Purpose: define the operating contract for the runtime-home source pack under `resources/home/user/**`.

This contract applies to `resources/home/user` and every child path unless a deeper `AGENTS.md` overrides it.

## Mission
- Keep the runtime-home source pack coherent, fast to route, and correct for the installed Codex layout.
- Treat `resources/home/user/**` as pack source material, not as a scratch area or speculative runtime dump.
- Favor concise, high-signal documentation that helps the next agent pick one correct path quickly.

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
2) Load memory only when the task is repo-aware, ambiguous, or depends on prior decisions.
3) Route through `$CODEX_HOME/INDEX.md`.
4) Read `$CODEX_HOME/index/pack/plans.md` and `$CODEX_HOME/index/pack/workflows.md`.
5) Load only the minimum skills required.
6) Follow `$CODEX_HOME/UNIX.md` before shell-sensitive work.
7) Open one concrete entrypoint, then stop broad browsing.

## Source-of-truth map
- `resources/home/user/INDEX.md` is the top router for the runtime pack.
- `resources/home/user/index/manifest.yml` is the routing metadata source for index entrypoints and related-link intent.
- `resources/home/user/docs/**` contains the runtime documentation source.
- `resources/home/user/plans/**` contains the plan template source.
- `resources/home/user/.models/**` contains model catalog and instruction-source assets referenced by runtime config.
- `resources/home/user/docs/create-prompts.md` owns the prompt-file catalog and direct prompt-file references for this tree.

## Documentation rules
- Keep top-level routing docs concise. Route first, dive deeper only when needed.
- Update cross-links in the same change when files move or canonical paths change.
- If a doc references a runtime path, verify that path exists in the current source pack or clearly qualify it as optional.
- Do not leave stale machine-specific repository references in user-facing guidance.
- Do not leave unresolved placeholders in non-template docs, plans, or workflow guides.
- Prefer one canonical explanation for a concept instead of repeating it across multiple overview files.

## Index and routing rules
- When changing pack entrypoint semantics, update both the rendered entrypoint doc and `resources/home/user/index/manifest.yml` when the canonical target or related-link contract changes.
- Keep one clear purpose per overview file:
  - `INDEX.md` chooses a router
  - `index/OVERVIEW.md` explains routing behavior
  - router overviews choose one entrypoint
  - docs/plans/workflows overviews explain catalog structure and usage
- Stop once the right router or entrypoint is chosen. Do not turn overviews into encyclopedias.

## Prompt asset rules
- Prompt asset files must be Markdown.
- The first line of every prompt file must be a short HTML comment describing the prompt.
- Prompt assets should be concise, directive, and reusable as direct Codex requests.
- Keep all direct prompt-file references centralized in `docs/create-prompts.md`.

## Shell and runtime rules
- For shell-sensitive work, explicitly invoke the matching shell and keep shell-specific assets honest about their supported runtime.
- Read `$CODEX_HOME/UNIX.md` before running shell-sensitive commands.
- Use deterministic commands and machine-readable output where possible.
- Prefer read-only discovery first, then the smallest deterministic change.

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
- When touching the governing pack files (`AGENTS.md`, `INDEX.md`, `docs/**`, `index/**`, `plans/**`, `resources/skills/**`), also run focused contract checks for stale links or structural drift.
- If you skip a check, say exactly why and name the next command that should run.

## Multi-agent guidance
- Use the role model in `$CODEX_HOME/MULTI_AGENT.md`.
- Prefer role-oriented language over tool-specific control primitives unless the active runtime explicitly provides those primitives.
- Keep ownership boundaries explicit: one owner for the final patch, separate owners only for genuinely independent discovery or validation slices.

## Output contract
- Return: Summary -> Tests -> Risks/Follow-ups -> Next steps.
- Include concrete file references with line numbers for the important edits.
- State assumptions explicitly when behavior depends on credentials, permissions, or optional runtime assets.
