# Documentation hub
Purpose: provide the top-level map for runtime-pack documentation and tell the agent when to stop browsing.

## Navigation
<!-- BEGIN:nav -->
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Use this file when
- you need a map of the documentation tree
- you are deciding which documentation domain to open next
- you are maintaining docs and need to confirm the top-level structure

## Do not use this file when
- you already know the correct router or entrypoint
- the task is clearly pack, domain, or workflow specific

## Documentation areas
<!-- BEGIN:contents -->
- `$CODEX_HOME/docs/containers/overview.md` — Containers overview
- `$CODEX_HOME/docs/desktop/overview.md` — Desktop stack overview
- `$CODEX_HOME/docs/filesystems/overview.md` — Filesystems overview
- `$CODEX_HOME/docs/infra/overview.md` — Infrastructure overview
- `$CODEX_HOME/docs/lang/overview.md` — Languages overview
- `$CODEX_HOME/docs/observability/overview.md` — Observability overview
- `$CODEX_HOME/docs/perf/overview.md` — Performance playbook
- `$CODEX_HOME/docs/security/overview.md` — Security overview
- `$CODEX_HOME/docs/style/overview.md` — Style guides
- `$CODEX_HOME/docs/system/overview.md` — Host hardening overview
- `$CODEX_HOME/docs/systemd/overview.md` — systemd overview
- `$CODEX_HOME/docs/templates/overview.md` — Templates overview
- `$CODEX_HOME/docs/virtualization/overview.md` — Virtualization overview
- `$CODEX_HOME/docs/vscode/overview.md` — VS Code overview
- `$CODEX_HOME/docs/web/overview.md` — Web frameworks overview
- `$CODEX_HOME/docs/workflows/overview.md` — Workflows overview
- `$CODEX_HOME/docs/architecture.md` — Architecture notes
- `$CODEX_HOME/docs/create-prompts.md` — Prompt file design guide
- `$CODEX_HOME/docs/prompt-writing.md` — Prompt writing
- `$CODEX_HOME/docs/prompts-maintenance.md` — Prompt maintenance
<!-- END:contents -->

## Runtime-pack browsing order
1. Route with `$CODEX_HOME/INDEX.md`.
2. Use the correct `index/**/overview.md` router.
3. Open one documentation entrypoint or one domain overview from this tree.
4. Only then open deeper docs.

## Maintenance rules
- Keep docs operational, concrete, and path-correct.
- Use `$CODEX_HOME` / `$CODEX_SKILLS` style runtime paths instead of installer-repo paths.
- Keep prompt-file references centralized in `$CODEX_HOME/docs/create-prompts.md`.
- Validate links and format-specific files after editing.

## Related
- `$CODEX_HOME/index/pack/docs.md`
- `$CODEX_HOME/index/pack/workflows.md`
- `$CODEX_HOME/MULTI_AGENT.md`
