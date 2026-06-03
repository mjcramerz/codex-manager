# Create prompts
Purpose: define how runtime prompt files under `$CODEX_HOME/.prompt/` should be written, reviewed, and maintained.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Scope
- This is the only documentation file under `resources/home/user/*` that should directly reference prompt files in `$CODEX_HOME/.prompt/`.
- Use it when creating, revising, or reviewing reusable prompt assets intended for Codex requests.

## Current prompt files
- `$CODEX_HOME/.prompt/codex-general.md`
- `$CODEX_HOME/.prompt/bugfix.md`
- `$CODEX_HOME/.prompt/feature-implementation.md`
- `$CODEX_HOME/.prompt/code-review.md`
- `$CODEX_HOME/.prompt/docs-refresh.md`
- `$CODEX_HOME/.prompt/shell-runtime.md`
- `$CODEX_HOME/.prompt/windows-manager.md`

## File contract
- Every prompt file must be Markdown.
- The first line must be a short HTML comment that describes the prompt in one sentence.
- The body should be ready to paste into a Codex request with minimal editing.
- Keep the wording concrete, directive, and operational rather than conversational.

## Design rules
- Start with the role and domain depth that the task actually needs.
- State the task objective early.
- Require read-first behavior before edits.
- Call out the critical constraints explicitly: correctness, security, compatibility, rollout, or testing.
- Prefer deterministic instructions over vague requests such as “improve this” or “make it better”.
- Keep prompts concise enough to scan quickly, but detailed enough to drive the full task without extra interpretation.

## Recommended structure
1. Short top comment.
2. Role statement.
3. Task objective.
4. Boundaries and non-goals.
5. Validation expectations.
6. Reporting expectations.

## What to avoid
- Machine-specific repository references.
- Environment-secret requests or broad environment dumps.
- Ambiguous success criteria.
- Hidden assumptions about shell runtime, operating system, or deployment target.
- Instructions that encourage destructive changes without explicit confirmation.

## Review checklist
- Does the prompt clearly state what Codex should do?
- Does it preserve behavior unless change is explicitly requested?
- Does it tell Codex to inspect the current repository state before editing?
- Does it require concrete validation?
- Is the wording concise enough to reuse directly?

## Maintenance notes
- Keep prompt file names lower-case and hyphenated.
- When adding a new prompt file, update this document and nowhere else in `resources/home/user/*`.
- If prompt guidance changes broadly, update this document first and then adjust the affected prompt files.
