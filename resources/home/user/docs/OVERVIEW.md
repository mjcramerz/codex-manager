# Documentation hub
Purpose: provide the top-level map for runtime-pack documentation and help the agent stop browsing quickly.

## Navigation
<!-- BEGIN:nav -->
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Use this file when
- you need a map of the documentation tree
- you are deciding which documentation area to open next
- you are maintaining docs and need to confirm the top-level structure

## Primary documentation areas
<!-- BEGIN:contents -->
- `$CODEX_HOME/docs/workflows/overview.md` — Operational workflows
- `$CODEX_HOME/docs/style/overview.md` — Shell and language conventions
- `$CODEX_HOME/docs/lang/overview.md` — Language-focused guidance
- `$CODEX_HOME/docs/templates/overview.md` — Template guidance
- `$CODEX_HOME/docs/architecture.md` — Runtime-pack architecture
- `$CODEX_HOME/docs/create-prompts.md` — Prompt-file design guide
- `$CODEX_HOME/docs/plugins.md` — Runtime plugins and marketplace guidance
<!-- END:contents -->

## Split of responsibility
- You use `$CODEX_HOME/docs/**` for concise runtime-pack routing.
- You use `/data/codex/docs/**` when you need full host, installation, or administrative procedures.
- When a runtime-pack doc routes to `/data/codex/docs/**`, follow that path for the detailed steps instead of expanding them here.

## Repo-aligned workflow shortcuts
- Codex installer/runtime repo -> `$CODEX_HOME/docs/workflows/codex-manager.md`
- Repo-aware memory routing -> `$CODEX_HOME/memories/MEMORY.md`
- Podman MCP stack repo -> `$CODEX_HOME/docs/workflows/codex-mcp.md`
- Cloudflare + GitLab delivery repos -> `$CODEX_HOME/docs/workflows/cloudflare-delivery.md`
- Debian installer repo -> `$CODEX_HOME/docs/workflows/debian-preseed.md`
- Runtime-pack maintenance -> `$CODEX_HOME/docs/workflows/runtime-pack-maintenance.md`

## Maintenance rules
- Keep docs operational, concrete, and path-correct.
- Use `$CODEX_HOME`, `$CODEX_AGENTS`, and `$CODEX_SKILLS` runtime paths instead of repository-source paths unless the repo itself is the subject.
- Keep prompt-file references centralized in `$CODEX_HOME/docs/create-prompts.md`.
- Keep documentation focused on stable pack surfaces; route memory-specific work through `$CODEX_HOME/memories/MEMORY.md` when needed.
