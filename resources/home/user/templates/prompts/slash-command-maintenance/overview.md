# Slash command prompt maintenance template
Use this template when creating or refactoring slash-command prompt files.

## Inputs
- Command name (for example `/my_command`).
- Purpose, boundaries, and acceptance criteria.
- Required arguments and `$ARGUMENTS` contract.
- Linked routing/workflow/plan/skill references.

## Outputs
- `prompt-template.md` adapted for the target command.
- Updated entry in `$CODEX_HOME/prompts/OVERVIEW.md`.
- Validation evidence from prompt and pack checks.

## Steps
1) Copy `prompt-template.md` into `$CODEX_HOME/prompts/<command>.md`.
2) Fill objective, constraints, inputs, and verification sections.
3) Confirm referenced entrypoints and maintenance assets are current.
4) Run prompt checks, then pack checks.

## Next steps
- Update `$CODEX_HOME/docs/workflows/prompts-library.md` if maintenance flow changed.
- Update `$CODEX_HOME/snippets/docs/prompt_contract.md` if contract conventions changed.
- Use skill `pack-prompts` for larger prompt-library edits.
