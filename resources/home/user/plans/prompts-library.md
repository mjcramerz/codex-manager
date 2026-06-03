# Plan

Use this plan when adding, updating, or removing prompt assets in the pack source tree.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/plans/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Requirements
- Make prompt changes in source at `$CODEX_HOME/prompts/*` (not runtime copies).
- Keep command coverage and argument contracts explicit in each prompt file.
- Preserve deterministic verification and routing behavior after edits.

## Scope
- In: prompt files and prompt index content under `$CODEX_HOME/prompts/`.
- Out: unrelated skill/template/doc implementation changes.

## Files and entry points
- `$CODEX_HOME/docs/prompts-maintenance.md`
- `$CODEX_HOME/docs/workflows/prompts-library.md`
- `$CODEX_HOME/plans/workflows/workflow-prompts-library.md`
- `$CODEX_HOME/prompts/OVERVIEW.md`
- `$CODEX_HOME/prompts/*.md`
- `$CODEX_HOME/templates/prompts/slash-command-maintenance/`
- `$CODEX_HOME/snippets/docs/prompt_contract.md`
- Use skill `pack-prompts`.

## Action items
[ ] Define prompt objective, required inputs, and expected outputs before editing.
[ ] Update prompt source files only under `$CODEX_HOME/prompts/*`.
[ ] Keep prompt-maintenance workflow/plan/template/snippet references aligned when contracts change.
[ ] Validate command naming, argument placeholders, and linked entrypoints.

## Testing and validation

## Security checkpoints
- Ensure prompts do not instruct bypassing auth, validation, or safety constraints.
- Keep network/destructive actions explicit and bounded.
- Avoid embedding secrets or environment dumps in prompt content.

## Testing checkpoints
- Confirm every changed prompt remains discoverable through `prompts/OVERVIEW.md`.
- Verify no stale references remain after rename/remove operations.
- Re-run prompt checks after any follow-up edits.

## Deployment checkpoints
- Sync runtime copies only after source validation passes.
- Record changed commands and migration notes for users.
- Confirm rollback path (restore prior prompt files) before release.

## Multi-agent handoff
- Coordinator assigns ownership by prompt file set and stop condition.
- Executor reports updated prompt paths, validation output, and unresolved gaps.
- Receiver confirms source-of-truth remained `$CODEX_HOME/prompts/*`.

## Risks and edge cases
- Command name drift between filename and overview listing.
- Broken entrypoint links after routing/index refactors.
- Runtime/source divergence if sync is skipped or partial.

## Open questions
- None.
