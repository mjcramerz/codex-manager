# Plan catalog
Purpose: explain when a plan is required and how to choose the correct plan family.

## Navigation
<!-- BEGIN:nav -->
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Use a plan before coding when
- the task is ambiguous, risky, or cross-cutting
- multiple files, systems, or teams are involved
- rollout, rollback, migration, or operational impact matters
- the work touches external systems, contracts, or long validation chains

## Choose one plan family
<!-- BEGIN:contents -->
- `$CODEX_HOME/plans/frameworks/overview.md` — Plan frameworks (overview)
- `$CODEX_HOME/plans/skills/overview.md` — Skill plans (overview)
- `$CODEX_HOME/plans/workflows/overview.md` — Workflow plans (overview)
- `$CODEX_HOME/plans/docs-and-workflows.md` — Plan
- `$CODEX_HOME/plans/index-and-routing.md` — Plan
- `$CODEX_HOME/plans/pack-overview.md` — Plan
- `$CODEX_HOME/plans/prompts-library.md` — Plan
- `$CODEX_HOME/plans/rules-library.md` — Plan
- `$CODEX_HOME/plans/scripts-and-verification.md` — Plan
- `$CODEX_HOME/plans/skills-library.md` — Plan
- `$CODEX_HOME/plans/snippets-library.md` — Plan
- `$CODEX_HOME/plans/templates-library.md` — Plan
<!-- END:contents -->

## Universal plan requirements
- Objective and user-visible outcome
- Scope and explicit non-goals
- Current-state inventory: files, entrypoints, systems, or datasets
- Ordered action items with verification checkpoints
- Security, reliability, and rollback considerations
- Concrete validation commands and expected evidence

## Quality gates for non-trivial plans
- Define dependencies, owners, and assumptions
- Define measurable success criteria and exit conditions
- Capture operational readiness: observability, runbooks, post-change verification
- Capture API or integration contracts, retries/timeouts, and error handling when applicable
- Capture rollback conditions before risky changes begin

## Plan families
- Framework plans: feature, bugfix, refactor, migration, performance, security, integration, infra, docs
- Workflow plans: execution checklists tied to workflow playbooks
- Skill plans: repeatable checklists tied to a specific skill

## Maintenance rules
- Keep plan overviews free of unresolved placeholders.
- If the runtime pack does not ship a catalog or directory, do not reference it as required.
- When you add a new plan template, list it in the correct overview in the same change.

## Related
- `$CODEX_HOME/index/pack/plans.md`
- `$CODEX_HOME/index/core/plan.md`
