# Prompts maintenance
Guidance for creating and maintaining slash-command prompt assets from pack source.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Scope
- Source of truth: `$CODEX_HOME/prompts/*`
- Runtime mirrors: `$CODEX_HOME/prompts/*` (materialized, not source)

## Use this guide for
- adding a new slash command prompt
- refining existing prompt argument contracts (`$ARGUMENTS`)
- removing or renaming prompts safely
- updating prompt-maintenance support assets (routing, workflow, template, snippet, skill)

## Maintenance bundle
- Workflow: `$CODEX_HOME/docs/workflows/prompts-library.md`
- Workflow plan: `$CODEX_HOME/plans/workflows/workflow-prompts-library.md`
- Library plan: `$CODEX_HOME/plans/prompts-library.md`
- Skill: `pack-prompts`
- Template: `$CODEX_HOME/templates/prompts/slash-command-maintenance/`
- Snippet: `$CODEX_HOME/snippets/docs/prompt_contract.md`

## Verification
- `rg -n --sort path --color=never '\$ARGUMENTS' $CODEX_HOME/prompts`
- Run the narrowest full validation command available for the active Codex worktree.

## Notes
- Keep command naming deterministic and avoid hidden side effects in prompt instructions.
- Keep links to entrypoints, plans, and skills current when files move.
- Prefer minimal, reviewable prompt diffs with explicit acceptance criteria.
