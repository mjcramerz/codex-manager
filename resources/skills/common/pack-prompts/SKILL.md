---
name: pack-prompts
description: Create or update slash-command prompts under $CODEX_HOME/prompts/. Use when
  adding prompt commands, tightening argument contracts, or improving prompt-library maintenance
  assets.
metadata:
  version: '1.0'
  short-description: Maintain pack prompts and prompt-maintenance assets
  tags:
  - pack-prompts
  - prompts
  - pack
interface:
  display-name: PACK-Prompts
  short-description: Maintain pack prompts and prompt-maintenance assets
  icon-small: assets/icon-32.png
  icon-large: assets/icon-128.png
  brand-color: '#CC6A32'
  default-prompt: Act as the "PACK-Prompts" specialist for "Maintain pack prompts and prompt-maintenance
    assets". Deliver focused, deterministic results with minimal, reviewable changes and explicit
    assumptions. Validate untrusted inputs and bounded I/O, run the narrowest relevant checks,
    and report concrete actions, evidence, and residual risks.
---

# PACK-Prompts

## Use this skill when
- creating, updating, or retiring files in `$CODEX_HOME/prompts/`
- tightening `{{args}}` contracts, command naming, or prompt invocation guidance
- adding prompt-maintenance support assets (workflow docs, plans, templates, snippets, routing links)
- validating prompt-library consistency after pack routing or index changes

## Inputs
- target prompt command(s) and expected invocation contract
- required linked assets (workflow docs, plans, templates, snippets, index links)
- compatibility constraints for existing command names and argument placeholders

## Scope and boundaries
- Edit source prompt files under `$CODEX_HOME/prompts/`, not runtime copies.
- Keep prompt contracts explicit; avoid hidden assumptions in free-form args.
- Preserve existing command names unless renaming is explicitly requested.

## Workflow
1) Define the prompt objective, required inputs, and acceptance criteria.
2) Edit source-of-truth prompt assets only in `$CODEX_HOME/prompts/*`.
3) Update prompt-maintenance routing/docs/plans/templates/snippets as needed for discoverability.
5) Summarize changed prompt commands, contract changes, and follow-up actions.

## Prompt maintenance guardrails
- Keep prompt command names stable unless a rename is explicitly requested.
- Keep `{{args}}` placeholders explicit and avoid ambiguous free-form contracts.
- Ensure prompt docs point to pack source (`$CODEX_HOME/prompts/*`), not runtime mirrors.
- Avoid instructing bypasses for auth, validation, or destructive operations.

## Agent orchestration
- Delegate read-only inventory checks for prompt/link coverage only.
- Keep one owner for prompt contract edits and verification.

## Validation and testing

## Outputs
- Actionable prompt-library edits aligned to user intent.
- Updated prompt-maintenance assets (workflow, plan, template, snippet, and routing links) when required.
- Verification evidence from prompt checks and pack-level checks.

## References
- `$CODEX_HOME/prompts/OVERVIEW.md`
- `references/latest-sources.md`
