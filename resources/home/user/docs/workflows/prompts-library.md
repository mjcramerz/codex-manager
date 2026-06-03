# Prompts library workflow

Start with `$CODEX_HOME/plans/workflows/workflow-prompts-library.md` before executing this workflow.
Purpose: maintain slash-command prompts and prompt-maintenance assets from source under `$CODEX_HOME/prompts/`.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/workflows/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Plan

Use `$CODEX_HOME/plans/prompts-library.md` for prompt-library maintenance scope and `$CODEX_HOME/plans/workflows/workflow-prompts-library.md` for workflow execution.

## Source-of-truth rules
- Edit prompts in `$CODEX_HOME/prompts/*` only.
- Do not treat runtime copies under `$CODEX_HOME/prompts/*` as authoritative.
- Keep slash command names stable unless rename is explicitly requested.
- Keep `$ARGUMENTS` contracts explicit and consistent with command behavior.

## Maintenance flow
1) Confirm objective, affected commands, and expected behavior.
2) Update prompt source files and prompt catalog entries.
3) Update supporting maintenance assets (template, snippet, skill docs, routing links) when contracts change.
4) Run prompt-focused checks before pack-wide checks.

## Validation sequence
- `rg -n --sort path --color=never '\$ARGUMENTS' $CODEX_HOME/prompts`
- Run the narrowest full validation command available for the active Codex worktree.

## Security checkpoints
- Reject prompt changes that encourage bypassing auth, validation, or destructive safeguards.
- Keep input constraints explicit (required args, bounded scope, expected verification).
- Ensure prompt guidance does not leak secrets or request environment dumps.

## Testing checkpoints
- Verify updated commands are listed in `$CODEX_HOME/prompts/OVERVIEW.md`.
- Validate links to entrypoints, plans, and skills after renames or file moves.
- Re-run prompt checks after each follow-up edit to avoid stale references.

## Deployment checkpoints
- Sync runtime prompt copies only after source checks pass.
- Document renamed/retired commands and migration notes for users.
- Keep rollback path available by preserving prior prompt revisions.

## Multi-agent handoff
- Coordinator assigns command/file ownership and success criteria.
- Executor reports changed prompt files, validation evidence, and unresolved gaps.
- Receiver verifies source-of-truth remained `$CODEX_HOME/prompts/*` before next step.

See also:
- `$CODEX_HOME/plans/prompts-library.md`
- `$CODEX_HOME/docs/prompts-maintenance.md`
- `$CODEX_HOME/index/pack/prompts.md`
- Use skill `pack-prompts`.
